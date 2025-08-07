from fastapi import APIRouter, Depends
from app.schema.chat_schema import (
    CreateGuestChatRequest,
    SendGuestMessageRequest,
    CreateUserChatRequest,
    SendUserMessageRequest,
    UpdateUserChatRequest,
    UpdateUserMessageRequest,
)
import app.services.chat_service as chat_service
from app.utils.auth import get_current_user, AuthData

chat_router = APIRouter()


# User Chat Endpoints
@chat_router.post("/user")
async def create_user_chat(
    chat: CreateUserChatRequest, auth_data: AuthData = Depends(get_current_user)
):
    """Create a new user chat."""
    result = await chat_service.create_user_chat(chat, auth_data.user_id)
    return {"success": True, "message": "Chat created successfully", "data": result}


@chat_router.get("/user")
async def get_user_chats(
    auth_data: AuthData = Depends(get_current_user)
):
    """Retrieve all user chats."""
    result = await chat_service.get_user_chats(auth_data.user_id)
    return {"success": True, "message": "Chats retrieved successfully", "data": result}


@chat_router.get("/{chat_id}/user")
async def get_user_chat(
    chat_id: str, 
    auth_data: AuthData = Depends(get_current_user)
):
    """Retrieve a specific user chat by chat ID."""
    result = await chat_service.get_user_chat(chat_id, auth_data.user_id)
    return {"success": True, "message": "Chat retrieved successfully", "data": result}


@chat_router.get("/{chat_id}/user/messages")
async def get_user_chat_messages(
    chat_id: str, 
    auth_data: AuthData = Depends(get_current_user)
):
    """Retrieve messages from a specific user chat."""
    result = await chat_service.get_user_chat_messages(chat_id, auth_data.user_id)
    return {
        "success": True,
        "message": "Messages retrieved successfully",
        "data": result,
    }


@chat_router.delete("/{chat_id}/user")
async def delete_user_chat(
    chat_id: str, 
    auth_data: AuthData = Depends(get_current_user)
):
    """Delete a specific user chat by chat ID."""
    result = await chat_service.delete_user_chat(chat_id, auth_data.user_id)
    return {"success": True, "message": "Chat deleted successfully", "data": result}


@chat_router.put("/{chat_id}/user")
async def update_user_chat(
    chat_id: str, chat: UpdateUserChatRequest, auth_data: AuthData = Depends(get_current_user)
):
    """Update a specific user chat by chat ID."""
    result = await chat_service.update_user_chat(chat_id, chat, auth_data.user_id)
    return {"success": True, "message": "Chat updated successfully", "data": result}


@chat_router.post("/{chat_id}/user/message")
async def send_user_message(
    chat_id: str,
    message: SendUserMessageRequest,
    auth_data: AuthData = Depends(get_current_user),
):
    """Send a message in a specific user chat."""
    result = await chat_service.send_user_message(chat_id, auth_data.user_id, message)
    return {"success": True, "message": "Message sent successfully", "data": result}


@chat_router.put("/{chat_id}/user/message/{message_id}")
async def update_user_message(
    chat_id: str,
    message_id: str,
    data: UpdateUserMessageRequest,
    auth_data: AuthData = Depends(get_current_user),
):
    """Update a specific user message by message ID."""
    result = await chat_service.update_user_message(chat_id, message_id, data, auth_data.user_id)
    return {"success": True, "message": "Message updated successfully", "data": result}