from fastapi import APIRouter
from app.pipeline.reset_chroma import reset_chroma_collection
from app.pipeline.cleanup_mongodb import cleanup_mongodb
from datetime import datetime
import logging


reset_chroma_router = APIRouter()

@reset_chroma_router.post("/")
def reset_chroma():
    success =  reset_chroma_collection()
    return {"success": success}


reset_mongo_router = APIRouter()

@reset_mongo_router.post("/")
def reset_mongo():
    logging.info(f"Resetting MongoDB... {datetime.now()}")
    success = cleanup_mongodb()
    return {"success": success}
    
