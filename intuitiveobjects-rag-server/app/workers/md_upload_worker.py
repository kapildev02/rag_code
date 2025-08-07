from app.db.mongodb import (
    connect_to_mongodb,
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
from docling.document_converter import DocumentConverter
from app.utils.pages_wise_metadata import processor


async def get_pdf_from_gridfs(gridfs_id: str) -> bytes:
    raw_gridfs_file = await get_fs().open_download_stream(ObjectId(gridfs_id))
    raw_pdf_bytes = await raw_gridfs_file.read()
    return raw_pdf_bytes

# def split_pdf_from_bytes(pdf_bytes: bytes, folder_name: str, output_folder=settings.SPLITED_PDF_FOLDER_PATH):
#     """Split a multi-page PDF from bytes into separate files using doc_id as folder name."""
#     print(f"Splitting PDF into pages for folder: {output_folder}")
#     pdf_folder = Path(output_folder) / folder_name
#     pdf_folder.mkdir(parents=True, exist_ok=True)

#     pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
#     output_paths = []

#     for page_num in range(len(pdf_doc)):
#         output_path = pdf_folder / f"page_{page_num + 1}.pdf"
#         new_pdf = fitz.open()
#         new_pdf.insert_pdf(pdf_doc, from_page=page_num, to_page=page_num)
#         new_pdf.save(output_path)
#         new_pdf.close()
#         output_paths.append(str(output_path))

#     return output_paths

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


# async def convert_and_upload_markdown(
#     doc_id: str, 
#     user_id: str, 
#     split_pages_root=settings.SPLITED_PDF_FOLDER_PATH, 
#     output_root=settings.MD_FILE_FOLDER_PATH
# ):
#     source_folder = Path(split_pages_root) / doc_id

#     converter = DocumentConverter()

#     for filename in sorted(os.listdir(source_folder)):
#         if filename.lower().endswith(".pdf"):
#             page_number = int(filename.split('_')[1].split('.')[0])
#             source_path = source_folder / filename
#             output_filename = filename.replace(".pdf", ".md")

#             result = converter.convert(Path(source_path))
            
#             await document_collection().update_one(
#                 {"_id": ObjectId(doc_id)},
#                 {
#                     "$set": {
#                         "current_stage": "PDF_TO_MD_CONVERTED",
#                         "updated_at": datetime.now(),
#                     },
#                     "$push": {
#                         "status_history": {
#                             "stage": "PDF_TO_MD_CONVERTED",
#                             "status": "completed",
#                             "timestamp": datetime.now(),
#                             "error_message": None,
#                             "retry_count": 0
#                         }
#                     }
#                 }
#             )
#             await rabbitmq_client.send_message(
#                 settings.NOTIFY_QUEUE,
#                 json.dumps({
#                     "event_type": "document_notify",
#                     "doc_id": doc_id,
#                     "user_id": user_id,
#                 })
#             )
            
#             if result and result.document:
#                 # Save markdown locally (optional, for backup/debugging)
#                 local_md_path = Path(output_root) / doc_id
#                 local_md_path.mkdir(parents=True, exist_ok=True)

#                 full_local_path = local_md_path / output_filename
                
#                 result.document.save_as_markdown(Path(full_local_path))


#                 # Read and upload content to GridFS
#                 with open(full_local_path, "rb") as f:
#                     md_bytes = f.read()

#                 gridfs_id = await upload_markdown_to_gridfs(
#                     doc_id, output_filename, md_bytes, page_number
#                 )
                
#                 print(f"Uploaded Markdown page {page_number} to GridFS with id: {gridfs_id}")
#             else:
#                 print(f"Conversion failed for: {source_path}")


async def convert_and_upload_markdown(
    doc_id: str, 
    user_id: str, 
    input_root=settings.SPLITED_PDF_FOLDER_PATH, 
    output_root=settings.MD_FILE_FOLDER_PATH
):
    source_folder = Path(input_root) / doc_id

    converter = DocumentConverter()

    for filename in sorted(os.listdir(source_folder)):
        if filename.lower().endswith((".pdf", ".docx", ".pptx", ".xml", ".txt")):  # Add other file types as needed
            source_path = source_folder / filename
            output_filename = filename.rsplit('.', 1)[0] + ".md"

            result = converter.convert(Path(source_path))
            
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
                # Save markdown locally (optional, for backup/debugging)
                local_md_path = Path(output_root) / doc_id
                local_md_path.mkdir(parents=True, exist_ok=True)

                full_local_path = local_md_path / output_filename
                
                result.document.save_as_markdown(Path(full_local_path))

                # Read and upload content to GridFS
                with open(full_local_path, "rb") as f:
                    md_bytes = f.read()

                gridfs_id = await upload_markdown_to_gridfs(
                    doc_id, output_filename, md_bytes, page_number=0  # Use 0 or None for non-page-specific files
                )
                
                print(f"Uploaded Markdown for {filename} to GridFS with id: {gridfs_id}")
            else:
                print(f"Conversion failed for: {source_path}")

async def on_message(task: aio_pika.IncomingMessage):
    try:
        message = json.loads(task.body.decode())
        
        print(f"TASK: doc: {message["doc_id"]}")
        
        # doc id
        doc_id = message["doc_id"]
        user_id = message["user_id"]
        
        doc_result = await document_collection().find_one(
            ObjectId(doc_id)
        )
        
        if not doc_result:
            print(f"{doc_id} document not found")
            
        fs_file_cursor = get_fs().find({
            "metadata.doc_id": doc_id, 
            "metadata.doc_type": "RAW"
        })
        fs_files = await fs_file_cursor.to_list(length=1)
            
        fs_file = fs_files[0]
        raw_gridfs_id = fs_file["_id"]
        
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
        pdf_bytes = await get_pdf_from_gridfs(raw_gridfs_id)
        print(f"PDF bytes length: {len(pdf_bytes)}")
        # Split PDF pages and save to folder named after doc_id
        # output_paths = split_pdf_from_bytes(pdf_bytes=pdf_bytes, folder_name=doc_id)
        
        # if not output_paths:
            # raise
        
        await convert_and_upload_markdown(doc_id, user_id)
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
        
        await processor.index_pdf(converted_md_files, "Employee Data base", doc_id, user_id)
        

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