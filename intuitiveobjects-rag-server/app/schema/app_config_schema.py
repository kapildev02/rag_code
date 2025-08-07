from pydantic import BaseModel
from typing import List

class ModelOption(BaseModel):
    label: str
    value: str

class CreateAppConfigRequest(BaseModel):
    llm_model: List[ModelOption]
    embedding_model: List[ModelOption]