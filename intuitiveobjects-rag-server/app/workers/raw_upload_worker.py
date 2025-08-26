from app.db.mongodb import (
    connect_to_mongodb,
    organization_file_collection,
    document_collection,
    get_fs
)
from app.core.rabbitmq_client import rabbitmq_client
from app.core.config import settings
import asyncio
import aio_pika
import json
from bson import ObjectId
from app.utils.google import get_google_credentials
from googleapiclient.discovery import build
from datetime import datetime
from io import BytesIO
from googleapiclient.http import MediaIoBaseDownload
import hashlib


async def on_message(task: aio_pika.IncomingMessage):
    try:
        message = json.loads(task.body.decode())
        print(f"TASK: doc: {message['doc_id']}")

        # doc id
        doc_id = message["doc_id"]
        user_id = message["user_id"]
        
        # get user google drive credentials
        creds = await get_google_credentials(user_id=user_id)
        
        # check if the google drive crdentials exist
        if not creds:
            await document_collection().update_one(
                {"_id": ObjectId(doc_id)},
                {
                    "$set": {
                        "current_stage": "ACCESS_DENIED",
                        "updated_at": datetime.now(),
                    },
                    "$push": {
                        "status_history": {
                            "stage": "ACCESS_DENIED",
                            "status": "completed",
                            "timestamp": datetime.now(),
                            "error_message": "google token expired",
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
            await task.ack()
            return

        doc_result = await document_collection().find_one(
            ObjectId(doc_id)
        )
        
        if not doc_result:
            print(f"{doc_id} document not found")
            
        # build drive service 
        drive_service = build('drive', 'v3', credentials=creds)
    
        
        file_request = drive_service.files().get_media(fileId=doc_result["file_id"])
        
        # download file
        file_data = BytesIO()
        downloader = MediaIoBaseDownload(file_data, file_request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Download progress: {int(status.progress() * 100)}%")
        file_data.seek(0)
        
        
        hash_key = hashlib.sha256(file_data.getvalue()).hexdigest()
        print(f"hash_key: {hash_key}")

        is_duplicate = await document_collection().find_one({
            "hash_key": hash_key,
            "organization_id": doc_result["organization_id"],
            "current_stage": "COMPLETED"
        })
        
        if is_duplicate:
            await document_collection().update_one(
                {"_id": ObjectId(doc_id)},
                {
                    "$set": {
                        "current_stage": "FILE_ALREADY_EXISTS_SKIPPED",
                        "updated_at": datetime.now(),
                    },
                    "$push": {
                        "status_history": {
                            "stage": "FILE_ALREADY_EXISTS_SKIPPED",
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
            await task.ack()
            return


        await document_collection().update_one(
            {"_id": ObjectId(doc_id)},
            {
                "$set": {
                    "current_stage": "RAW_FILE_UPLOAD_STARTED",
                    "updated_at": datetime.now(),
                    "hash_key": hash_key
                },
                "$push": {
                    "status_history": {
                        "stage": "RAW_FILE_UPLOAD_STARTED",
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
        grid_fs_id = await get_fs().upload_from_stream(
            doc_result["filename"],
            file_data,
            metadata={
                "type": doc_result["mime_type"],
                "organization_id": doc_result["organization_id"],
                "uploaded_by": user_id,
                "doc_id": doc_id,
                "doc_type": "RAW",
                "source": "GOOGLE_DRIVE",
                "uploaded_at": datetime.now()
            }
        )


        await document_collection().update_one(
            {"_id": ObjectId(doc_id)},
            {
                "$set": {
                    "current_stage": "RAW_FILE_UPLOAD_UPLOADED",
                    "updated_at": datetime.now(),
                },
                "$push": {
                    "status_history": {
                        "stage": "RAW_FILE_UPLOAD_UPLOADED",
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
        file_size_bytes = len(file_data.getvalue())
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        rabbitmq_job = message
                
        await rabbitmq_client.send_message(
            settings.MD_FILE_CONVERSION_QUEUE,
            json.dumps(rabbitmq_job)
        )

        await document_collection().update_one(
            {"_id": ObjectId(doc_id)},
            {
                "$set": {
                    "current_stage": "MD_CONVERSION_JOB_QUEUED",
                    "updated_at": datetime.now(),
                },
                "$push": {
                    "status_history": {
                        "stage": "MD_CONVERSION_JOB_QUEUED",
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
        print(f"Uploaded to GridFS: {doc_result["filename"]} ({file_size_mb:.2f} MB) with gridfsId: {grid_fs_id}")
        
        # Manually ack after successful processing
        await task.ack()
    except Exception as e:
        print(f"Processing failed: {e}")
        await task.ack()


async def main():
    await connect_to_mongodb()
    await rabbitmq_client.connect()
    await rabbitmq_client.channel.set_qos(prefetch_count=1)
    
    # Start consuming (non-blocking, async)
    await rabbitmq_client.consume_message(settings.GOOGLE_DRIVE_FILE_UPLOAD_QUEUE, on_message)
    await asyncio.Future()
    
    
if __name__ == "__main__":
    asyncio.run(main())