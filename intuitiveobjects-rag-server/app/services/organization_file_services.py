from app.models.organization_file_model import OrganizationFile
from fastapi import UploadFile, HTTPException
from app.db.mongodb import (
    organization_admin_collection,
    organization_file_collection,
    get_fs,
    document_collection,
    ingestion_status_collection,
    get_client
)
from bson import ObjectId
import os
import io
from app.core.config import settings
from app.serializers.organization_file_serializers import (
    OrganizationFileEntity,
    OrganizationFileListEntity,
)
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List
import hashlib
from datetime import datetime
from app.core.rabbitmq_client import rabbitmq_client
import json
from app.schema.organization_file_schema import UploadGoogleDriveSchema
from app.utils.google import get_google_credentials


async def organization_upload_file(
    category_id: str, file: UploadFile, tags: List[str], user_id: str
):
    existing_organization_admin = await organization_admin_collection().find_one(
        {"_id": ObjectId(user_id)}
    )

    if not existing_organization_admin:
        raise HTTPException(status_code=404, detail="Organization admin not found")


    file_name = file.filename
    file_size = file.size
    file_type = file.content_type
    
    # Save the file content to GridFS
    grid_in = await get_fs().upload_from_stream(
        file.filename,
        file.file,
        metadata={"contentType": file_type, "organizationId": existing_organization_admin["organization_id"]}
    )

    file_data = OrganizationFile(
        organization_id=existing_organization_admin["organization_id"],
        category_id=category_id,
        file_name=file_name,
        file_type=file_type,
        file_size=file_size,
        tags=tags,
        storage_id=str(grid_in)  # Save the GridFS file ID
    )


    result = await organization_file_collection().insert_one(file_data.model_dump())

    new_file = await organization_file_collection().find_one(
        {"_id": result.inserted_id}
    )

    return OrganizationFileEntity(new_file)


async def organization_get_files(user_id: str):
    existing_organization_admin = await organization_admin_collection().find_one(
        {"_id": ObjectId(user_id)}
    )

    if not existing_organization_admin:
        raise HTTPException(status_code=404, detail="Organization admin not found")

    files = (
        await document_collection()
        .find({"organization_id": existing_organization_admin["organization_id"]})
        .to_list(None)
    )

    return OrganizationFileListEntity(files)


async def organization_delete_file(file_id: str, user_id: str):
    existing_organization_admin = await organization_admin_collection().find_one(
        {"_id": ObjectId(user_id)}
    )

    if not existing_organization_admin:
        raise HTTPException(status_code=404, detail="Organization admin not found")

    print("Deleting file:", file_id)
    existing_file = await organization_file_collection().find_one(
        {
            "_id": ObjectId(file_id),
            "organization_id": existing_organization_admin["organization_id"],
        }
    )

    if not existing_file:
        raise HTTPException(status_code=404, detail="File not found")

    await organization_file_collection().delete_one({"_id": ObjectId(file_id)})

    return OrganizationFileEntity(existing_file)


async def organization_google_drive_upload_file(
    files_data: UploadGoogleDriveSchema,
    user_id: str
):
    # get existing org admin for organization id
    existing_org_admin = await organization_admin_collection().find_one({
        "_id": ObjectId(user_id)
    })
    
    # check organization admin exists
    if not existing_org_admin:
        raise HTTPException(status_code=404, detail="Organization admin not found")
    
    # check filedata exists in payload
    if not files_data.files or len(files_data.files) == 0:
        raise HTTPException(status_code=400, detail="Files required")
    
    # check the file allowed files
    if not len(files_data.files) <= settings.MAX_FILES_PER_FOLDER:
        raise HTTPException(status_code=400, detail=f"{settings.MAX_FILES_PER_FOLDER} files only allowed")
    
    # get user google drive credentials
    creds = await get_google_credentials(user_id=user_id)
    
    # check if the google drive crdentials exist
    if not creds:
        raise HTTPException(status_code=400, detail="Google Invalid or expired credentials")
    
    # build drive service 
    drive_service = build('drive', 'v3', credentials=creds)
    
    processed_files = []
    rejected_files = []
    
    # loop through the files
    for file_id in files_data.files:
        try:
            # get file meta data
            file_meta_data = drive_service.files().get(
                    fileId=file_id,
                    fields="id, name, mimeType, size"
                ).execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise HTTPException(status_code=404, detail="File not found")
            raise HTTPException(status_code=400, detail=f"Error accessing file: {e}")
        
        file_mime_type = file_meta_data.get("mimeType")
        file_name = file_meta_data.get("name", "Unknowm")
        file_size = file_meta_data.get("size", "Unknown")
        mime_type = file_meta_data.get("mimeType", "Unknown")
        
        # check file type is valid
        if(file_mime_type != "application/pdf"):
            rejected_files.append({
                "filename": file_name,
                "reason": f"Invalid file type {file_mime_type}"
            })
            continue
        
        # check file size
        if int(file_size) > settings.MAX_FILE_SIZE:
            rejected_files.append({
                "filename": file_name,
                "reason": f"File size exceeds {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB limit"
            })
            continue
        
        # create one document with status
        new_doc = {
            "organization_id": existing_org_admin["organization_id"],
            "category_id": files_data.category_id,
            "filename": file_name,
            "file_size": file_size,
            "mime_type": mime_type,
            "file_id": file_id,
            "tags": files_data.tags or [],
            "hash_key": None,
            "source_type": "GOOGLE_DRIVE",
            "current_stage": None,
            "status_history": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        
        # insert into database
        doc_result = await document_collection().insert_one(
            new_doc
        )
        
        # insert into queue
        rabbitmq_job = {
            "doc_id": str(doc_result.inserted_id),
            "user_id": user_id
        }
                
        await rabbitmq_client.send_message(
            settings.GOOGLE_DRIVE_FILE_UPLOAD_QUEUE,
            json.dumps(rabbitmq_job)
        )
        
        # update status
        update_data = {
            "$set": {
                "current_stage": "UPLOAD_JOB_QUEUED",
                "updated_at": datetime.now(),
            },
            "$push": {
                "status_history": {
                    "stage": "UPLOAD_JOB_QUEUED",
                    "status": "completed",
                    "timestamp": datetime.now(),
                    "error_message": None,
                    "retry_count": 0
                }
            }
        }

        await document_collection().update_one(
            {"_id": doc_result.inserted_id},
            update_data
        )

        updated_doc = await document_collection().find_one(
            {"_id": doc_result.inserted_id}
        )

        processed_files.append(
            OrganizationFileEntity(updated_doc)
        )
            
    return processed_files
    
    

async def organization_local_drive_upload(
    category_id: str,
    files: List[UploadFile],
    tags: List[str],
    user_id: str
): 
    existing_org_admin = await organization_admin_collection().find_one({
        "_id": ObjectId(user_id)
    })
    
    if not existing_org_admin:
        raise HTTPException(status_code=404, detail="Organization admin not found")
    
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="Files required")
    
    if not len(files) <= settings.MAX_FILES_PER_FOLDER:
        raise HTTPException(status_code=400, detail="10 files only allowed")
        
    processed_files = []
    rejected_files = []
    
    for file in files:
        content = await file.read()
        
        # validate the file size
        if len(content) > settings.MAX_FILE_SIZE:
            rejected_files.append({
                "filename": file.filename,
                "reason": f"File size exceeds {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB limit"
            })
            continue
        
        new_doc = {
            "organization_id": existing_org_admin["organization_id"],
            "category_id": category_id,
            "filename": file.filename,
            "file_size": file.size,
            "mime_type": file.content_type,
            "file_id": None,
            "tags": tags or [],
            "hash_key": None,
            "source_type": "LOCAL_DRIVE",
            "current_stage": None,
            "status_history": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        
        # insert into database
        doc_result = await document_collection().insert_one(
            new_doc
        )
        
        # update status
        update_data = {
            "$set": {
                "current_stage": "UPLOAD_JOB_QUEUED",
                "updated_at": datetime.now(),
            },
            "$push": {
                "status_history": {
                    "stage": "UPLOAD_JOB_QUEUED",
                    "status": "completed",
                    "timestamp": datetime.now(),
                    "error_message": None,
                    "retry_count": 0
                }
            }
        }

        await document_collection().update_one(
            {"_id": doc_result.inserted_id},
            update_data
        )
    
        # create the file hash
        hash_key = hashlib.sha256(content).hexdigest()
        
        # check if the file already exist for the organization
        is_duplicate = await document_collection().find_one({
            "hash_key": hash_key,
            "organization_id": existing_org_admin["organization_id"],
            "current_stage": "COMPLETED"
        })
        
        # if duplicate reject the file
        if is_duplicate:
            await document_collection().update_one(
                {"_id": doc_result.inserted_id},
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

            doc =  await document_collection().find_one(
                {"_id": doc_result.inserted_id}
            )
            processed_files.append(OrganizationFileEntity(doc))    
            continue

        await document_collection().update_one(
            {"_id": doc_result.inserted_id},
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
        
        grid_fs_id = await get_fs().upload_from_stream(
            new_doc["filename"],
            content,
            metadata={
                "type": new_doc["mime_type"],
                "organization_id": new_doc["organization_id"],
                "uploaded_by": user_id,
                "doc_id": str(doc_result.inserted_id),
                "doc_type": "RAW",
                "source": "LOCAL_DRIVE",
                "uploaded_at": datetime.now()
            }
        )

        await document_collection().update_one(
            {"_id": doc_result.inserted_id},
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
        
        rabbitmq_job = {
            "doc_id": str(doc_result.inserted_id),
            "user_id": user_id,
        }
                
        await rabbitmq_client.send_message(
            settings.MD_FILE_CONVERSION_QUEUE,
            json.dumps(rabbitmq_job)
        )

        await document_collection().update_one(
            {"_id": doc_result.inserted_id},
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

        doc = await document_collection().find_one(
            {"_id": doc_result.inserted_id}
        )
        processed_files.append(OrganizationFileEntity(doc))
    
    return processed_files