from pydantic import BaseModel


class EmailSchema(BaseModel):
    name: str
    phone: str
    email: str
    message: str
