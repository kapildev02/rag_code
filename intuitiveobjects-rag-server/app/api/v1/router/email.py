from fastapi import APIRouter, HTTPException
from app.schema.email_schema import EmailSchema
import app.services.email_services as email_services

email_router = APIRouter()


@email_router.post("/contact")
async def contact_us(emailData: EmailSchema):
    try:
        await email_services.contact_us(emailData)
        return {"message": "Email sent successfully", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
