from pydantic import BaseModel, EmailStr, Field
from typing import List

class UploadGoogleDriveSchema(BaseModel):
    files: List[str]
    category_id: str
    tags: List[str] = Field(default_factory=list)