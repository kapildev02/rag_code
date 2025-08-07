from app.schema.email_schema import EmailSchema
from fastapi_mail import FastMail, MessageSchema
from app.core.mail_config import conf
from fastapi import HTTPException
from app.core.config import settings


async def contact_us(emailData: EmailSchema):
    try:
        body = (
            f"🧑 Name: {emailData.name}\n"
            f"📧 Email: {emailData.email}\n\n"
            f"📝 Query:\n{emailData.message}"
        )
        message = MessageSchema(
            subject="Contact Us",
            recipients=[settings.EMAIL_USER],
            body=body,
            subtype="plain",
        )
        fm = FastMail(conf)
        await fm.send_message(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
