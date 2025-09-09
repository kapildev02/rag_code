from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
import app.schema.organization_admin_schema as organization_admin_schema
import app.services.organization_admin_services as organization_admin_services
from app.utils.auth import get_current_user, AuthData
from app.utils.google import get_google_auth_flow
from fastapi.responses import RedirectResponse, JSONResponse
from app.core.config import settings
from app.db.mongodb import google_auth_collection
from app.utils.google import get_google_credentials

organization_admin_router = APIRouter()


@organization_admin_router.post("/organization/{organization_id}")
async def create_organization_admin(
    organization_id: str,
    organization_admin: organization_admin_schema.CreateOrganizationAdminSchema,
):
    try:
        organization_admin = (
            await organization_admin_services.create_organization_admin(
                organization_id, organization_admin
            )
        )
        return {
            "message": "Organization admin created successfully",
            "success": True,
            "data": organization_admin,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@organization_admin_router.get("/organization/{organization_id}")
async def get_organization_admin(organization_id: str):
    try:
        organization_admin = await organization_admin_services.get_organization_admins(
            organization_id
        )
        return {
            "message": "Organization admin retrieved successfully",
            "success": True,
            "data": organization_admin,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@organization_admin_router.put("/{organization_admin_id}")
async def update_organization_admin(
    organization_admin_id: str,
    organization_admin: organization_admin_schema.UpdateOrganizationAdminSchema,
):
    try:
        organization_admin = (
            await organization_admin_services.update_organization_admin(
                organization_admin_id, organization_admin
            )
        )
        return {
            "message": "Organization admin updated successfully",
            "success": True,
            "data": organization_admin,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@organization_admin_router.delete("/{organization_admin_id}")
async def delete_organization_admin(organization_admin_id: str):
    try:
        organization_admin = (
            await organization_admin_services.delete_organization_admin(
                organization_admin_id
            )
        )
        return {
            "message": "Organization admin deleted successfully",
            "success": True,
            "data": organization_admin,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@organization_admin_router.post("/login")
async def login_organization_admin(
    organization_admin: organization_admin_schema.LoginOrganizationAdminSchema,
):
    try:
        organization_admin = await organization_admin_services.login_organization_admin(
            organization_admin
        )
        return {
            "message": "Organization admin logged in successfully",
            "success": True,
            "data": organization_admin,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@organization_admin_router.post("/category")
async def create_category(
    category: organization_admin_schema.CreateCategorySchema,
    auth_data: AuthData = Depends(get_current_user),
):
    try:
        category = await organization_admin_services.create_category(category, auth_data.user_id)
        return {
            "message": "Category created successfully",
            "success": True,
            "data": category,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@organization_admin_router.get("/category")
async def get_categories(auth_data: AuthData = Depends(get_current_user)):
    try:
        categories = await organization_admin_services.get_categories(auth_data.user_id)
        return {
            "message": "Categories retrieved successfully",
            "success": True,
            "data": categories,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@organization_admin_router.get("/category/{category_id}")
async def get_category(category_id: str, auth_data: AuthData = Depends(get_current_user)):
    try:
        category = await organization_admin_services.get_category_name(category_id, auth_data.user_id)
        return {
            "message": "Category retrieved successfully",
            "success": True,
            "data": category,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 


@organization_admin_router.put("/category/{category_id}")
async def update_category(
    category_id: str,
    category: organization_admin_schema.UpdateCategorySchema,
    auth_data: AuthData = Depends(get_current_user),
):
    try:
        category = await organization_admin_services.update_category(
            category_id, category, auth_data.user_id
        )
        return {
            "message": "Category updated successfully",
            "success": True,
            "data": category,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@organization_admin_router.delete("/category/{category_id}")
async def delete_category(category_id: str, auth_data: AuthData = Depends(get_current_user)):
    try:
        category = await organization_admin_services.delete_category(
            category_id, auth_data.user_id
        )
        return {
            "message": "Category deleted successfully",
            "success": True,
            "data": category,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@organization_admin_router.post("/organization-app-config")
async def create_organization_app_config(
    organization_app_config: organization_admin_schema.CreateOrganizationAppConfigSchema,
    auth_data: AuthData = Depends(get_current_user),
):
    try:
        organization_app_config = (
            await organization_admin_services.create_organization_app_config(
                organization_app_config, auth_data.user_id
            )
        )
        return {
            "message": "Organization app config created successfully",
            "success": True,
            "data": organization_app_config,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@organization_admin_router.get("/organization-app-config")
async def get_organization_app_config(auth_data: AuthData = Depends(get_current_user)):
    try:
        organization_app_config = await organization_admin_services.get_organization_app_configs(auth_data.user_id)
        return {
            "message": "Organization app config retrieved successfully",
            "success": True,
            "data": organization_app_config,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
@organization_admin_router.get("/google/auth")
async def google_auth(auth_data: AuthData = Depends(get_current_user)):
    try:
        flow = get_google_auth_flow(auth_data.token)
        auth_url, _ = flow.authorization_url(
            prompt="consent", 
            access_type="offline",
            include_granted_scopes="true"
        )

        return {
            "message": "Goole auth initiated",
            "success": True,
            "data":{
                "auth_url": auth_url
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@organization_admin_router.get("/google/oauth2/callback")
async def google_oauth2_callback(request: Request):
    try:
        token = request.query_params.get("state")
        
        auth_data = get_current_user(token)
        
        # Extract authorization response
        flow = get_google_auth_flow(token)
        authorization_response = str(request.url)
        
        # Fetch token
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials
        
        # google credentials
        google_auth_details = {
            "user_id": auth_data.user_id,
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "token_uri": credentials.token_uri,
            "scopes": credentials.scopes,
            "created_at": datetime.now().isoformat(),
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None
        }
        
        await google_auth_collection().insert_one(
            google_auth_details
        )
        
        return RedirectResponse(settings.FRONTEND_URL)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@organization_admin_router.get("/google/list-files")
async def list_files(auth_data: AuthData = Depends(get_current_user), page_size: int = 20):
    """List files from user's Google Drive."""
    try:
        creds = await get_google_credentials(auth_data.user_id)

        if not creds:
            raise HTTPException(status_code=400, detail="Google auth not found")
        
        # Build Drive service
        service = build('drive', 'v3', credentials=creds)
        
        # List files
        results = service.files().list(
            pageSize=min(page_size, 100),  # Limit to prevent abuse
            fields="nextPageToken, files(id, name, size, mimeType, modifiedTime, webViewLink)",
            orderBy="modifiedTime desc",
            q="mimeType='application/pdf'" 
        ).execute()
        
        files = results.get('files', [])
        print(files)
        
        # Format file information
        formatted_files = []
        for file in files:
            formatted_files.append({
                "id": file['id'],
                "name": file['name'],
                "size": file.get('size', 'Unknown'),
                "mimeType": file.get('mimeType', 'Unknown'),
                "modifiedTime": file.get('modifiedTime', 'Unknown'),
                "webViewLink": file.get('webViewLink', '')
            })
        
        
        return JSONResponse({
            "message": "Goole auth initiated",
            "success": True,
            "data": {
                "files": formatted_files,
                "total": len(formatted_files),
                "nextPageToken": results.get('nextPageToken')
            }
        })
        
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@organization_admin_router.get("/profile")
async def get_organization_admin_profile(auth_data: AuthData = Depends(get_current_user)):
    try:
        profile = await organization_admin_services.get_organization_admin_profile(auth_data.user_id)
        return {
            "message": "Organization admin profile retrieved successfully",
            "success": True,
            "data": profile,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@organization_admin_router.delete("/google/auth")
async def disconnect_google_auth(auth_data: AuthData = Depends(get_current_user)):
    try:
        result = await organization_admin_services.disconnect_google_auth(auth_data.user_id)
        return {
            "message": "Google Drive account disconnected successfully",
            "success": True,
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))