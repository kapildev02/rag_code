import os
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List

load_dotenv()


class Settings(BaseModel):
    # API settings
    PROJECT_NAME: str = "Demo API"
    API_V1_STR: str = "/api/v1"

    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "secret_key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # MongoDB settings
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    MONGODB_DB: str = os.getenv("MONGODB_DB")
    MONGODB_USER: str = os.getenv("MONGODB_USER")
    MONGODB_PASSWORD: str = os.getenv("MONGODB_PASSWORD")
    MONGODB_TIMEOUT: int = 3000

    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER")
    IMAGE_URL: str = os.getenv("IMAGE_URL")
    EMAIL_USER: str = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD")
    GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE: str = os.getenv(
        "GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE"
    )
    
    # RabbitMQ settings
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST")
    RABBITMQ_PORT: int = os.getenv("RABBITMQ_PORT")
    RABBITMQ_USERNAME: str = os.getenv("RABBITMQ_USERNAME")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD")
    FILE_PROCESSING_CHANNEL: str = os.getenv("FILE_PROCESSING_CHANNEL")
    
    # File Configuration
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))
    MAX_FILES_PER_FOLDER: int = int(os.getenv("MAX_FILES_PER_FOLDER", "20"))
    ALLOWED_FILE_EXTENSIONS: List[str] = [".pdf"]
    
    # GOOGLE DRIVE SETTINGS
    GOOGLE_CLIENT_SECRET_FILE: str = os.getenv("GOOGLE_CLIENT_SECRET_FILE")
    SCOPES: List[str] = ["https://www.googleapis.com/auth/drive.readonly"]
    GOOGLE_REDIRECT_URI: str = "http://127.0.0.1:8000/api/v1/organization-admin/google/oauth2/callback"
    FRONTEND_URL: str = "http://localhost:5173/admin"

    GOOGLE_DRIVE_FILE_UPLOAD_QUEUE: str = os.getenv("GOOGLE_DRIVE_FILE_UPLOAD_QUEUE")
    MD_FILE_CONVERSION_QUEUE: str= os.getenv("MD_FILE_CONVERSION_QUEUE")
    NOTIFY_QUEUE: str = os.getenv("NOTIFY_QUEUE")
    SPLITED_PDF_FOLDER_PATH: str = os.getenv("SPLITED_PDF_FOLDER_PATH", "splited_pdf_pages")
    MD_FILE_FOLDER_PATH: str = os.getenv("MD_FILE_FOLDER_PATH", "output_md_files")
    

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
