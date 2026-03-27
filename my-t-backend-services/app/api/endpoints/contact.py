from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.core.data.database import db_manager
from app.logger.app_logger import app_logger

router = APIRouter()


class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    message: str


@router.post("/", status_code=status.HTTP_201_CREATED)
async def submit_contact_message(payload: ContactMessage):
    """Store a contact form submission."""
    app_logger.log_info(f"[Contact] New message from {payload.email}")
    try:
        doc = {
            "name": payload.name,
            "email": payload.email,
            "message": payload.message,
            "created_at": datetime.utcnow(),
            "read": False,
        }
        db_manager.db["contact_messages"].insert_one(doc)
        app_logger.log_info(f"[Contact] Message saved from {payload.email}")
        return {"message": "Your message has been received. We'll get back to you soon!"}
    except Exception as e:
        app_logger.log_error(f"[Contact] Failed to save message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit message. Please try again."
        )
