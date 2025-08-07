from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
from typing import List, Optional
from enum import Enum
class OrganizationFile(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    organization_id: str
    category_id: str
    file_name: str
    file_type: str = Field(default="")
    file_size: int = Field(default=0)
    type: str = Field(default="local")
    drive_file_id: str = Field(default="")
    drive_web_link: str = Field(default="")
    tags: List[str] = Field(default=[])
    storage_id: str = Field(default="")
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())
    
    
class SourceType(str, Enum):
    GDRIVE = "GDRIVE"
    LOCAL_FILE = "LOCAL_FILE"
    LOCAL_FOLDER = "LOCAL_FOLDER"
    SERVER_FOLDER = "SERVER_FOLDER"
    
class IngestionStatus(str, Enum):
    UPLOAD_INITIATED = "UPLOAD_INITIATED"
    SOURCE_VALIDATED = "SOURCE_VALIDATED"
    RAW_FILE_UPLOADED = "RAW_FILE_UPLOADED"
    JOB_QUEUED = "JOB_QUEUED"
    PROCESSING_STARTED = "PROCESSING_STARTED"
    MD_CONVERSION_COMPLETED = "MD_CONVERSION_COMPLETED"
    MD_FILE_SAVED = "MD_FILE_SAVED"
    CHUNKING_COMPLETED = "CHUNKING_COMPLETED"
    EMBEDDINGS_GENERATED = "EMBEDDINGS_GENERATED"
    MD_LOADED_IN_VECTORDB = "MD_LOADED_IN_VECTORDB"
    PROCESSING_COMPLETE = "PROCESSING_COMPLETE"
    ERROR_PROCESSING = "ERROR_PROCESSING"
    DUPLICATE_REJECTED = "DUPLICATE_REJECTED"
    SOURCE_ACCESS_ERROR = "SOURCE_ACCESS_ERROR"
    
class DocumentMetaData(BaseModel):
    file_name: str
    file_type: Optional[str] = None
    file_size: int
    folder_path: Optional[str] = None
    file_name: str = None
    
class Document(BaseModel):
    id: Optional[str] = Field(alias="_id")
    organization_id: str
    category_id: str
    hash_key: str
    source_type: SourceType
    tags: List[str] = Field(default=[])
    storage_id: str = Field(default="")
    ingestion_status: IngestionStatus = IngestionStatus.UPLOAD_INITIATED
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())
    tags: List[str] = Field(default=[])
    