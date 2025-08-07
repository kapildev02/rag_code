import os
from fastapi import HTTPException
from app.core.config import settings
from google_auth_oauthlib.flow import Flow
from google.auth.exceptions import RefreshError
from typing import Dict, Optional
from google.oauth2.credentials import Credentials
from app.db.mongodb import google_auth_collection
from fastapi import FastAPI, Request, HTTPException
from bson import ObjectId

def get_google_auth_flow(token: str):
    """Create and return OAuth2 flow object."""
    if not os.path.exists(settings.GOOGLE_CLIENT_SECRET_FILE):
        raise HTTPException(
            status_code=500, 
            detail=f"Client secret file '{settings.GOOGLE_CLIENT_SECRET_FILE}' not found. Please download it from Google Cloud Console."
        )
    
    return Flow.from_client_secrets_file(
        settings.GOOGLE_CLIENT_SECRET_FILE, 
        scopes=settings.SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
        state=token
    )
    
    
async def get_google_credentials(user_id: str) -> Optional[Credentials]:
    """Get and validate user credentials."""
    user_data = await google_auth_collection().find_one({
        "user_id": user_id
    })
    if not user_data:
        return None
    
    try:
        # Extract only valid Credentials parameters
        creds_data = {
            "token": user_data.get("token"),
            "refresh_token": user_data.get("refresh_token"),
            "token_uri": user_data.get("token_uri"),
            "client_id": user_data.get("client_id"),
            "client_secret": user_data.get("client_secret"),
            "scopes": user_data.get("scopes")
        }
        
        creds = Credentials(**creds_data)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

            await google_auth_collection().update_one(
                {
                    "user_id": user_id
                }, 
                {
                    "$set": {
                        "token": creds.token, 
                        "refresh_token": creds.refresh_token,
                    }
                }
            )
        return creds
    except RefreshError as e:
        print(f"Failed to refresh credentials for user {user_id}: {e}")
        # Remove invalid credentials
        await google_auth_collection().delete_one({
            "user_id": user_id
        })
        return None
    except Exception as e:
        print(f"Error creating credentials for user {user_id}: {e}")
        return None
