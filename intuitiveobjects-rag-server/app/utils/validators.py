from app.core.config import settings
import os
import hashlib

class DocumentValidator:
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        return  file_size <= settings.MAX_FILE_SIZE
    
    @staticmethod
    def validate_file_type(filename: str) -> bool:
        file_ext = os.path.splitext(filename)[1].lower()
        
        return file_ext in settings.ALLOWED_FILE_EXTENSIONS
    
    @staticmethod
    def generate_file_hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def generate_file_key(filename: str, organization_id: str) -> bool:
        return f"{organization_id}_{filename}"
    

document_validator = DocumentValidator()