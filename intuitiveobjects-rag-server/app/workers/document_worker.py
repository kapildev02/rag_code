# from app.db.mongodb import (
#     connect_to_mongodb,
#     organization_file_collection,
#     get_fs
# )
# from app.core.rabbitmq_client import rabbitmq_client
# from app.core.config import settings
# import asyncio
# import aio_pika
# import json
# from bson import ObjectId
# import markdownify
# import os
# import fitz 
# import io

# async def on_message(message: aio_pika.IncomingMessage):
#     try:
#         decoded_msg = json.loads(message.body.decode())
        
#         # doc id
#         doc_id = decoded_msg["doc_id"]
        
#         # check if doc id present or not
#         if not doc_id:
#             return
        
#         # fetch document details
#         doc = await organization_file_collection().find_one({
#             "_id": ObjectId(doc_id)
#         })
        
#         # check if the document present
#         if not doc:
#             return
        
#         # get gridfs raw file id
#         raw_gridfs_id = doc["raw_gridfs_id"]
        
#         # check raw_gridfs_id present
#         if not raw_gridfs_id:
#             return
        
#         # fetch the file from gridfs
#         raw_gridfs_file = await get_fs().open_download_stream(raw_gridfs_id)
#         raw_gridfs_file_bytes = await raw_gridfs_file.read()
        
#         # Open PDF using PyMuPDF
#         pdf_stream = io.BytesIO(raw_gridfs_file_bytes)
#         doc_pdf = fitz.open(stream=pdf_stream, filetype="pdf")
        
#         # Extract text from PDF
#         raw_txt = ""
#         for page in doc_pdf:
#             text = page.get_text("text")  # You can also try "html"
#             raw_txt += text + "\n\n"
            
#         doc_pdf.close()

#         # convert to markedown
#         md_text = markdownify.markdownify(raw_txt)
#         md_file_name = f"{doc['filename']}.md"
        
        
#         # Save Markdown file locally
#         local_dir = os.path.join("uploaded_local_files")
#         os.makedirs(local_dir, exist_ok=True)
#         local_file_path = os.path.join(local_dir, md_file_name)

#         with open(local_file_path, "w", encoding="utf-8") as f:
#             f.write(md_text)
            
#         print(f"md_file_name: {md_file_name}")
        
#         # Manually ack after successful processing
#         # await message.ack()
#     except Exception as e:
#         print(f"Processing failed: {e}")
#         # You can nack and optionally requeue the message
#         # await message.nack(requeue=True)


# async def main():
#     await connect_to_mongodb()
#     await rabbitmq_client.connect()
#     await rabbitmq_client.channel.set_qos(prefetch_count=1)
    
#     # Start consuming (non-blocking, async)
#     await rabbitmq_client.consume_message(settings.FILE_PROCESSING_CHANNEL, on_message)
#     await asyncio.Future()
    
    
# if __name__ == "__main__":
#     asyncio.run(main())

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
from docling.document_converter import DocumentConverter
from datetime import datetime
import os
from pathlib import Path

async def upload_markdown_to_gridfs(doc_id: str, filename: str, content: bytes):
    gridfs_id = await get_fs().upload_from_stream(
        filename,
        content,
        metadata={
            "doc_id": doc_id,
            "doc_type": "MD",
            "uploaded_at": datetime.now(),
            "type": "markdown"
        }
    )
    return gridfs_id

async def on_message(message: aio_pika.IncomingMessage):
    try:
        decoded_msg = json.loads(message.body.decode())
        doc_id = decoded_msg.get("doc_id")
        user_id = decoded_msg.get("user_id")
        
        # check if doc id present or not
        if not doc_id:
            return
        
        #fetch document details
        doc = await document_collection().find_one({"_id": ObjectId(doc_id)})

        # Check if document exists
        if not doc:
            return

        # get gridfs raw file id
        raw_gridfs_id = doc.get("raw_gridfs_id")

        if not raw_gridfs_id:
            return

        #fetch raw file from grids
        raw_file = await get_fs().open_download_stream(ObjectId(raw_gridfs_id))
        file_bytes = await raw_file.read()
        original_filename = doc.get("filename", "document")

        # Save temporarily
        temp_dir = Path(settings.SPLITED_PDF_FOLDER_PATH) / doc_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / original_filename

        with open(temp_path, "wb") as f:
            f.write(file_bytes)

        # Convert to Markdown
        converter = DocumentConverter()
        result = converter.convert(temp_path)

        if result and result.document:
            md_filename = original_filename.rsplit(".", 1)[0] + ".md"
            md_dir = Path(settings.MD_FILE_FOLDER_PATH) / doc_id
            md_dir.mkdir(parents=True, exist_ok=True)
            md_path = md_dir / md_filename

            result.document.save_as_markdown(md_path)

            with open(md_path, "rb") as f:
                md_bytes = f.read()

            gridfs_id = await upload_markdown_to_gridfs(doc_id, md_filename, md_bytes)
            print(f"Uploaded Markdown to GridFS with id: {gridfs_id}")

            # Update status
            await organization_file_collection().update_one(
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
        else:
            print(f"Conversion failed for: {temp_path}")

        await message.ack()

    except Exception as e:
        print(f"Processing failed: {e}")
        await message.ack()  # Or nack with requeue if needed

async def main():
    await connect_to_mongodb()
    await rabbitmq_client.connect()
    await rabbitmq_client.channel.set_qos(prefetch_count=1)
    await rabbitmq_client.consume_message(settings.FILE_PROCESSING_CHANNEL, on_message)
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
