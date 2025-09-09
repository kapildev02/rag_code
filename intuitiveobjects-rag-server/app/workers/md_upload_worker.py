from app.db.mongodb import (
    connect_to_mongodb,
    organization_file_collection,
    category_collection,
    document_collection,
    get_fs
)
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
os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"  # hide C++ backend logs
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # hide TensorFlow logs   
 

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
    Extracts and processes files from ZIP bytes.
    """
    # Create temporary directory for zip extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / original_filename
        
        # Write zip bytes to temporary file
        with open(zip_path, "wb") as f:
            f.write(file_bytes)

        # Extract and process files
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for file_info in zip_ref.filelist:
                if file_info.filename.startswith('__MACOSX') or file_info.filename.startswith('.'):
                    continue
                
                file_ext = Path(file_info.filename).suffix.lower().lstrip('.')
                if file_ext in [fmt.value for fmt in InputFormat]:
                    try:
                        # Extract single file to temp directory
                        extracted_path = Path(temp_dir) / file_info.filename
                        zip_ref.extract(file_info.filename, temp_dir)
                        
                        # Read extracted file
                        with open(extracted_path, 'rb') as f:
                            file_content = f.read()
                            
                        # Convert and upload each file
                        await convert_and_upload_markdown(
                            doc_id=doc_id,
                            user_id=user_id,
                            file_bytes=file_content,
                            original_filename=Path(file_info.filename).name
                        )
                        print(f"✅ Processed {file_info.filename} from zip")
                        
                    except Exception as e:
                        print(f"❌ Failed to process {file_info.filename}: {str(e)}")
                else:
                    print(f"⚠️ Skipping unsupported file type: {file_info.filename}")


async def convert_and_upload_markdown(doc_id: str, user_id: str, file_bytes: bytes, original_filename: str):
    
    temp_path = Path(settings.SPLITED_PDF_FOLDER_PATH) / f"{doc_id}_{original_filename}"
    temp_path.parent.mkdir(parents=True, exist_ok=True)

    # Save the file temporarily
    with open(temp_path, "wb") as f:
        f.write(file_bytes)
    
    
    converter = DocumentConverter()

    result = converter.convert(temp_path)

    await document_collection().update_one(
        {"_id": ObjectId(doc_id)},
        {
            "$set": {
                "current_stage": "FILE_TO_MD_CONVERTED",
                "updated_at": datetime.now(),
            },
            "$push": {
                "status_history": {
                    "stage": "FILE_TO_MD_CONVERTED",
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

    if result and result.document:
        output_filename = original_filename.rsplit(".", 1)[0] + ".md"
        local_md_path = Path(settings.MD_FILE_FOLDER_PATH) / doc_id
        local_md_path.mkdir(parents=True, exist_ok=True)
        full_local_path = local_md_path / output_filename

        result.document.save_as_markdown(full_local_path)

        with open(full_local_path, "rb") as f:
            md_bytes = f.read()

        gridfs_id = await upload_markdown_to_gridfs(doc_id, output_filename, md_bytes, page_number=1)
        print(f"Uploaded Markdown to GridFS with id: {gridfs_id} from md_worker")
    else:
        print(f"Conversion failed for: {temp_path}")


async def on_message(task: aio_pika.IncomingMessage):
    try:
        message = json.loads(task.body.decode())

        print(f"TASK: doc: {message["doc_id"]}, user: {message["user_id"]}")

        # doc id
        doc_id = message["doc_id"]
        
        user_id = message["user_id"]
        

        doc_result = await document_collection().find_one(
            ObjectId(doc_id)
        )

        tags = doc_result.get("tags", [])

        if not doc_result:
            print(f"{doc_id} document not found")

        category_id = doc_result.get("category_id", "unknown")
        result = await category_collection().find_one({"_id": ObjectId(category_id)})
        category = result.get("name", "unknown")
        print("Category :", category)

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
        # Split PDF pages and save to folder named after doc_id
        # output_paths = split_pdf_from_bytes(pdf_bytes=pdf_bytes, folder_name=doc_id)
        
        # if not output_paths:
            # raise


        # Fix here: use Path instead of path
        if Path(original_filename).suffix.lower() == ".zip":
            await process_zip_file(doc_id, user_id, file_bytes, original_filename)
        else:
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

        await processor.index_pdf(converted_md_files, category, doc_id, user_id,tags)

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