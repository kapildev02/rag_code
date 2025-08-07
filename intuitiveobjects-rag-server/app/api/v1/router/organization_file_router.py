from fastapi import APIRouter, UploadFile, File, Form, Depends
from app.utils import auth
from app.utils.auth import get_current_user,AuthData
import app.services.organization_file_services as organization_file_services
from typing import List
import json
from app.schema.organization_file_schema import UploadGoogleDriveSchema
import logging  
logger = logging.getLogger(__name__)

organization_file_router = APIRouter()

@organization_file_router.post("/upload")
async def upload_file(
    category_id: str = Form(...),
    file: UploadFile = File(...),
    tags: str = Form(...),
    auth_data: AuthData = Depends(get_current_user),
):
    tag_list = json.loads(tags)
    result = await organization_file_services.organization_upload_file(
        category_id, file, tag_list, auth_data.user_id
    )
    return {"message": "File uploaded successfully", "data": result}


@organization_file_router.get("/all")
async def get_files(auth_data: AuthData = Depends(get_current_user)):
    result = await organization_file_services.organization_get_files(auth_data.user_id)
    # logger.info(f"Fetched {result}--{len(result)} files for user {auth_data.user_id}")
    return {"message": "Files fetched successfully", "success": True, "data": result}


@organization_file_router.delete("/{file_id}")
async def delete_file(file_id: str, auth_data: AuthData = Depends(get_current_user)):
    result = await organization_file_services.organization_delete_file(file_id, auth_data.user_id)
    return {"message": "File deleted successfully", "success": True, "data": result}


@organization_file_router.post("/google-drive/upload")
async def upload_google_drive_file(
    files_data: UploadGoogleDriveSchema,
    auth_data: AuthData = Depends(get_current_user)
):
    result = await organization_file_services.organization_google_drive_upload_file(
        files_data,
        auth_data.user_id
    )
    return {
        "message": "File uploaded successfully", 
        "success": True, 
        "data": result
    }


@organization_file_router.post("/local-drive/upload")
async def upload_local_drive_file(
    category_id: str = Form(...),
    files: List[UploadFile] = Form(...),
    tags: List[str] = Form(...),
    auth_data: AuthData = Depends(get_current_user)
):
    
    result = await organization_file_services.organization_local_drive_upload(
        category_id,
        files,
        tags,
        auth_data.user_id
    )
    
    return {
        "message": "File uploaded successfully",
        "success": True,
        "data": result
    }