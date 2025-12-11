from app.db.mongodb import (
    connect_to_mongodb,
    organization_file_collection,
    category_collection,
    document_collection,
    get_fs
)
import pymupdf4llm
import tabula
from app.core.rabbitmq_client import rabbitmq_client
from app.core.config import settings
import asyncio
import aio_pika
import json
from bson import ObjectId
import fitz  
from pathlib import Path
from datetime import datetime
import os
import tempfile
import zipfile
from enum import Enum
from typing import List
import sys
from pathlib import Path
import os
import torch
os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"  # hide C++ backend logs
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # hide TensorFlow logs   
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Document converter using device: {DEVICE}")
from docling.document_converter import DocumentConverter
from app.utils.pages_wise_metadata import processor
import pathlib
import logging
logging.getLogger("docling").setLevel(logging.WARNING)
logging.getLogger("aio_pika").setLevel(logging.WARNING)
logging.getLogger("pika").setLevel(logging.WARNING)


async def get_pdf_from_gridfs(gridfs_id: str) -> bytes:
    raw_gridfs_file = await get_fs().open_download_stream(ObjectId(gridfs_id))
    raw_pdf_bytes = await raw_gridfs_file.read()
    return raw_pdf_bytes


def split_pdf_from_bytes(pdf_bytes: bytes, file_name: str, folder_name: str, output_folder=settings.SPLITED_PDF_FOLDER_PATH):
    """Split a multi-page PDF from bytes into separate files using doc_id as folder name."""
    print(f"Splitting PDF into pages for folder: {output_folder}")
    pdf_folder = Path(output_folder) / folder_name
    pdf_folder.mkdir(parents=True, exist_ok=True)

    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    output_paths = []
    # Clean filename by removing any special characters
    base_name = Path(file_name).stem.replace(" ", "_")
    for page_num in range(len(pdf_doc)):
        output_path = pdf_folder / f"{base_name}_{page_num + 1}.pdf"
        new_pdf = fitz.open()
        new_pdf.insert_pdf(pdf_doc, from_page=page_num, to_page=page_num)
        new_pdf.save(output_path)
        new_pdf.close()
        output_paths.append(str(output_path))

    pdf_doc.close()
    return output_paths


async def upload_markdown_to_gridfs(doc_id: str, filename: str, content: bytes, page_number: int):
    gridfs_id = await get_fs().upload_from_stream(
        filename,
        content,
        metadata={
            "doc_id": doc_id,
            "doc_type": "MD",
            "page_number": page_number,
            "uploaded_at": datetime.now(),
            "type": "markdown"
        }
    )
    return gridfs_id

class InputFormat(Enum):
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    CSV = "csv"
    PPT = "ppt"
    XLSX = "xlsx"
    PNG = "png"
    JPG = "jpg"

async def process_zip_file(doc_id: str, user_id: str, file_bytes: bytes, original_filename: str):
    """
    Extracts and processes files from ZIP bytes maintaining hierarchy.
    Each file in the ZIP gets its own subfolder within the main doc_id folder.
    """
    processed_files = {}
    
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / original_filename
        
        with open(zip_path, "wb") as f:
            f.write(file_bytes)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for file_info in zip_ref.filelist:
                if file_info.filename.startswith('__MACOSX') or file_info.filename.startswith('.'):
                    continue
                
                file_ext = Path(file_info.filename).suffix.lower().lstrip('.')
                if file_ext in [fmt.value for fmt in InputFormat]:
                    try:
                        # Create unique subfolder for each file
                        file_base_name = Path(file_info.filename).stem
                        subfolder_name = f"{file_base_name}"
                        
                        # Extract and process file
                        extracted_path = Path(temp_dir) / file_info.filename
                        zip_ref.extract(file_info.filename, temp_dir)
                        
                        with open(extracted_path, 'rb') as f:
                            file_content = f.read()
                        
                        # Split PDF and save in subfolder structure
                        output_paths = split_pdf_from_bytes(
                            pdf_bytes=file_content, 
                            file_name=subfolder_name,
                            folder_name=f"{doc_id}/{subfolder_name}"  # Nested structure
                        )
                        
                        processed_files[subfolder_name] = {
                            'paths': output_paths,
                            'original_name': file_info.filename,
                            'subfolder': subfolder_name
                        }
                        
                    except Exception as e:
                        print(f"❌ Failed to process {file_info.filename}: {str(e)}")
                else:
                    print(f"⚠️ Skipping unsupported file type: {file_info.filename}")

    # Process each subfolder maintaining hierarchy
    if processed_files:
        for subfolder_name, file_info in processed_files.items():
            try:
                await convert_and_upload_markdown(
                    doc_id=doc_id,
                    user_id=user_id,
                    file_bytes=file_bytes,
                    original_filename=file_info['original_name'],
                    subfolder=file_info['subfolder']
                )
                print(f"✅ Processed subfolder {subfolder_name}")
            except Exception as e:
                print(f"❌ Failed to process subfolder {subfolder_name}: {str(e)}")
    else:
        print("No files were successfully processed from the ZIP archive")

def wrap_markdown(text: str):
    class MarkdownWrapper:
        def __init__(self, content: str):
            self.document = self
            self.content = content.strip()

        def save_as_markdown(self, path: Path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.content)

    return MarkdownWrapper(text) if text else None

class MarkdownDocument:
    def __init__(self, content: str):
        self.document = self
        self.content = content.strip()

    def save_as_markdown(self, path: Path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.content)

async def convert_and_upload_markdown(doc_id: str, user_id: str, file_bytes: bytes, original_filename: str, subfolder: str = None):
    split_pages_root = settings.SPLITED_PDF_FOLDER_PATH
    output_root = settings.MD_FILE_FOLDER_PATH
    
    # Handle subfolder path if provided
    if subfolder:
        source_folder = Path(split_pages_root) / doc_id / subfolder
        output_folder = Path(output_root) / doc_id / subfolder
    else:
        source_folder = Path(split_pages_root) / doc_id
        output_folder = Path(output_root) / doc_id
    
    # Ensure output directory exists
    output_folder.mkdir(parents=True, exist_ok=True)

    converter = DocumentConverter()
    processed_count = 0

    sorted_files = sorted(os.listdir(source_folder), key=lambda x: int(x.rsplit('_', 1)[-1].split('.')[0]))

    for filename in sorted_files:
        try:
            # Extract page number from filename (assuming format name_X.pdf)
            name_parts = filename.rsplit('_', 1)
            if len(name_parts) != 2:
                    print(f"Skipping file with invalid format: {filename}")
                    continue
                    
            page_number = int(name_parts[1].split('.')[0])
            source_path = source_folder / filename
            output_filename = filename.replace(".pdf", ".md")

            result = None
            try:
                with fitz.open(str(source_path)) as doc:

                    for page in doc:  
                        text = page.get_text("text").strip()
                        blocks = page.get_text("blocks") or []
                        has_text = bool(text)
                        has_images = len(page.get_images(full=True)) > 0

                        # Try table detection via Tabula
                        has_table = False
                        try:
                            tables = tabula.read_pdf(str(source_path), pages=1, multiple_tables=True)
                            if tables and len(tables) > 0:
                                has_table = True
                        except Exception:
                            pass

                    # 🔹 Heuristic for complex layouts (realistic threshold)
                    block_count = len(blocks)
                    wide_blocks = sum(1 for b in blocks if b[2] - b[0] > 250 and b[3] - b[1] < 80)

                    # 👉 Complex only if block count > 25 (dense page) or several narrow rows (like a table)
                    complex_layout = block_count > 25 or wide_blocks > 5

                    # 🔹 Final decision
                    if has_images or has_table or not has_text or complex_layout:
                        print(f"🧠 Using Docling for Page (complex/table/image layout)")
                        result = converter.convert(Path(source_path))
                    else:
                        print(f"✍️ Using PyMuPDF for Page (simple text-only page)")
                        markdown_text = pymupdf4llm.to_markdown(Path(source_path))
                        # Create document-like object for consistent interface
                        result = MarkdownDocument(markdown_text)

            except Exception as e:
                print(f"Error processing {filename} with PyMuPDF: {e}")
                try:
                    result = converter.convert(Path(source_path))
                except Exception as e2:
                    print(f"Docling also failed for {filename}: {e2}")
                    continue

            if result and hasattr(result, 'document'):
                full_local_path = output_folder / output_filename
                result.document.save_as_markdown(full_local_path)

                with open(full_local_path, "rb") as f:
                    md_bytes = f.read()

                gridfs_id = await upload_markdown_to_gridfs(
                    doc_id, output_filename, md_bytes, page_number
                )

                print(f"✅ Uploaded Markdown page {page_number} to GridFS with id: {gridfs_id}")
            else:
                print(f"❌ No result generated for: {source_path}")

        except ValueError as e:
            print(f"Error processing {filename}: {e}")
            continue

    await document_collection().update_one(
        {"_id": ObjectId(doc_id)},
        {
            "$set": {
                "current_stage": "PDF_TO_MD_CONVERTED",
                "updated_at": datetime.now(),
            },
            "$push": {
                "status_history": {
                    "stage": "PDF_TO_MD_CONVERTED",
                    "status": "completed",
                    "timestamp": datetime.now(),
                    "error_message": None,
                    "retry_count": 0
                }
            }
        }
    )

    await rabbitmq_client.send_message(
        settings.NOTIFY_QUEUE,
        json.dumps({
            "event_type": "document_notify",
            "doc_id": doc_id,
            "user_id": user_id,
        })
    )

async def on_message(task: aio_pika.IncomingMessage):
    try:
        message = json.loads(task.body.decode())

        # doc id
        doc_id = message["doc_id"]
        #user id
        user_id = message["user_id"]

        print(f"Processing document ID: {doc_id} for user ID: {user_id}")

        doc_result = await document_collection().find_one(
            ObjectId(doc_id)
        )

        if not doc_result:
            print(f"{doc_id} document not found")

        category_id = doc_result.get("category_id", "unknown")
        result = await category_collection().find_one({"_id": ObjectId(category_id)})
        category = result.get("name", "unknown")
        tags = result.get("tags", [])
        source_type = doc_result.get("source_type", "unknown")

        print("Source Type :", source_type) 
        print("Category :", category)
        print("Tags :", tags)

        fs_file_cursor = get_fs().find({
            "metadata.doc_id": doc_id, 
            "metadata.doc_type": "RAW"
        })
        fs_files = await fs_file_cursor.to_list(length=1)

        if not fs_files:
            print(f"No raw file found for doc_id: {doc_id}")
            return
            
        fs_file = fs_files[0]
        raw_gridfs_id = fs_file["_id"]
        original_filename = fs_file["filename"]
    
        print(f"Processing file: {original_filename}")
 
        await document_collection().update_one(
            {"_id": ObjectId(doc_id)},
            {
                "$set": {
                    "current_stage": "MD_CONVERSION_JOB_STARTED",
                    "updated_at": datetime.now(),
                },
                "$push": {
                    "status_history": {
                        "stage": "MD_CONVERSION_JOB_STARTED",
                        "status": "completed",
                        "timestamp": datetime.now(),
                        "error_message": None,
                        "retry_count": 0
                    }
                }
            }
        )
        
        await rabbitmq_client.send_message(
            settings.NOTIFY_QUEUE,
            json.dumps({
                "event_type": "document_notify",
                "doc_id": doc_id,
                "user_id": user_id,
            })
        )
        
        # Fetch the file from gridfs
        # Download PDF bytes from GridFS
        file_bytes = await get_pdf_from_gridfs((raw_gridfs_id)) 
        print(f"PDF bytes length: {len(file_bytes)}")
        

        # Fix here: use Path instead of path
        if Path(original_filename).suffix.lower() == ".zip":
            await process_zip_file(doc_id, user_id, file_bytes, original_filename=original_filename)

        else:
             # Split PDF pages and save to folder named after doc_id
            output_paths = split_pdf_from_bytes(pdf_bytes=file_bytes, file_name=original_filename, folder_name=doc_id)
         
            if not output_paths:
                raise ValueError("No output paths returned from PDF splitting.")
            
            await convert_and_upload_markdown(doc_id, user_id, file_bytes, original_filename)

        await document_collection().update_one(
            {"_id": ObjectId(doc_id)},
            {
                "$set": {
                    "current_stage": "MD_FILE_UPLOADED",
                    "updated_at": datetime.now(),
                },
                "$push": {
                    "status_history": {
                        "stage": "MD_FILE_UPLOADED",
                        "status": "completed",
                        "timestamp": datetime.now(),
                        "error_message": None,
                        "retry_count": 0
                    }
                }
            }
        )
        await rabbitmq_client.send_message(
            settings.NOTIFY_QUEUE,
            json.dumps({
                "event_type": "document_notify",
                "doc_id": doc_id,
                "user_id": user_id,
            })
        )
        
        converted_md_files = Path(settings.MD_FILE_FOLDER_PATH) / doc_id
        print("converted_md_files", converted_md_files)

        await processor.index_pdf(converted_md_files, category, doc_id, user_id,tags, source_type)

        await document_collection().update_one(
            {"_id": ObjectId(doc_id)},
            {
                "$set": {
                    "current_stage": "COMPLETED",
                    "updated_at": datetime.now(),
                },
                "$push": {
                    "status_history": {
                        "stage": "COMPLETED",
                        "status": "completed",
                        "timestamp": datetime.now(),
                        "error_message": None,
                        "retry_count": 0
                    }
                }
            }
        )
        await rabbitmq_client.send_message(
            settings.NOTIFY_QUEUE,
            json.dumps({
                "event_type": "document_notify",
                "doc_id": doc_id,
                "user_id": user_id,
            })
        )
        print("File uploaded")
        # Manually ack after successful processing
        await task.ack()
    except Exception as e:
        print(f"Processing failed: {e}")
        # You can nack and optionally requeue the message
        await document_collection().update_one(
        {"_id": ObjectId(doc_id)},
        {
            "$set": {
                "current_stage": "Processing_Failed",
                "updated_at": datetime.now(),
            },
            "$push": {
                "status_history": {
                    "stage": "Processing_Failed",
                    "status": "Processing_Failed",
                    "timestamp": datetime.now(),
                    "error_message": None,
                    "retry_count": 0
                }
            }
        }
    )
        await task.ack()


async def main():
    await connect_to_mongodb()
    await rabbitmq_client.connect()
    await rabbitmq_client.channel.set_qos(prefetch_count=1)
    
    # Start consuming (non-blocking, async)
    await rabbitmq_client.consume_message(settings.MD_FILE_CONVERSION_QUEUE, on_message)
    await asyncio.Future()
    
    
if __name__ == "__main__":
    asyncio.run(main())