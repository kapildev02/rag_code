from pydantic import BaseModel, Field
from datetime import datetime


class OrganizationAdmin(BaseModel):
    name: str
    email: str
    password: str
    organization_id: str
    role: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())


class Category(BaseModel):
    name: str
    tags: list[str] = Field(default_factory=list)
    organization_id: str
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())

class OrganizationAppConfig(BaseModel):
    llm_model: str
    embedding_model: str
    system_prompt: str
    organization_id: str
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())
