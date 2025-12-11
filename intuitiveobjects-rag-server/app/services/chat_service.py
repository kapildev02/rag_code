from datetime import datetime
from app.schema.chat_schema import (
    CreateGuestChatRequest,
    SendGuestMessageRequest,
    CreateUserChatRequest,
    SendUserMessageRequest,
    UpdateUserChatRequest,
    UpdateUserMessageRequest,
)
from app.models.chat_model import Chat
from app.db.mongodb import chat_collection
from fastapi import HTTPException
from app.serializers.chat_serializers import chatEntity, chatListEntity
from app.models.message_model import Message, MessageRole
from app.db.mongodb import message_collection
from app.db.mongodb import user_query_collection
from app.utils.llm import expand_user_query
from app.serializers.message_serializers import messageListEntity, messageEntity
from bson.objectid import ObjectId
from app.utils.functions import inject_image_markdown
from app.utils.response_generator import generate_ai_response
import markdown
from app.data.questions import sample_question_and_answer
import logging
import json


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
    Create Guest Chat
"""


async def create_guest_chat(chat: CreateGuestChatRequest):
    try:
        new_chat = Chat(
            user_id=chat.user_id,
            name=chat.name,
        )

        result = await chat_collection().insert_one(new_chat.model_dump())

        if result.inserted_id is None:
            raise HTTPException(status_code=500, detail="Failed to create chat")

        created_chat = await chat_collection().find_one({"_id": result.inserted_id})

        return chatEntity(created_chat)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


"""
    Get Guest Chats
"""


async def get_guest_chats(user_id: str):
    try:
        chats = await chat_collection().find({"user_id": user_id}).to_list(length=100)
        return chatListEntity(chats)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


"""
    Get Guest Chat
"""


async def get_guest_chat(chat_id: str, user_id: str):
    try:
        chat = await chat_collection().find_one(
            {"_id": ObjectId(chat_id), "user_id": user_id}
        )
        return chatEntity(chat)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


"""
    Get Guest Chat Messages
"""


async def get_guest_chat_messages(chat_id: str, user_id: str):
    try:
        existing_chat = await chat_collection().find_one(
            {"_id": ObjectId(chat_id), "user_id": user_id}
        )
        if not existing_chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        messages = (
            await message_collection().find({"chat_id": chat_id}).to_list(length=100)
        )
        return messageListEntity(messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


"""
    Delete Guest Chat
"""


async def delete_guest_chat(chat_id: str, user_id: str):
    try:
        existing_chat = await chat_collection().find_one(
            {"_id": ObjectId(chat_id), "user_id": user_id}
        )
        if not existing_chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        result = await chat_collection().delete_one(
            {"_id": ObjectId(chat_id), "user_id": user_id}
        )
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Chat not found")
        return {"message": "Chat deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


"""
    Send Guest Message
"""


async def send_guest_message(
    chat_id: str, user_id: str, message: SendGuestMessageRequest
):
    try:
        existing_chat = await chat_collection().find_one(
            {"_id": ObjectId(chat_id), "user_id": user_id}
        )
        if not existing_chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        request_message = Message(
            chat_id=chat_id, content=message.content, role=MessageRole.user
        )

        ai_response = generate_ai_response(message.content)

        response_message = Message(
            chat_id=chat_id, content=ai_response, role=MessageRole.assistant
        )

        request_message_result = await message_collection().insert_one(
            request_message.model_dump()
        )

        if request_message_result.inserted_id is None:
            raise HTTPException(status_code=500, detail="Failed to send message")

        response_message_result = await message_collection().insert_one(
            response_message.model_dump()
        )

        if response_message_result.inserted_id is None:
            raise HTTPException(status_code=500, detail="Failed to send message")

        response_message = await message_collection().find_one(
            {"_id": response_message_result.inserted_id}
        )
        request_message = await message_collection().find_one(
            {"_id": request_message_result.inserted_id}
        )

        return {
            "response_message": messageEntity(response_message),
            "request_message": messageEntity(request_message),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


"""
    Create User Chat
"""


async def create_user_chat(chat: CreateUserChatRequest, user_id: str):
    try:
        new_chat = Chat(user_id=user_id, name=chat.name)

        chat_count = await chat_collection().count_documents({"user_id": user_id})

        new_chat.name = f"Chat {chat_count + 1}"

        result = await chat_collection().insert_one(new_chat.model_dump())

        if result.inserted_id is None:
            raise HTTPException(status_code=500, detail="Failed to create chat")

        created_chat = await chat_collection().find_one({"_id": result.inserted_id})

        return chatEntity(created_chat)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


"""
    Get User Chats
"""


async def get_user_chats(user_id: str):
    try:
        chats = await chat_collection().find({"user_id": user_id}).to_list(length=100)
        return chatListEntity(chats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


"""
    Get User Chat
"""


async def get_user_chat(chat_id: str, user_id: str):
    try:
        chat = await chat_collection().find_one(
            {"_id": ObjectId(chat_id), "user_id": user_id}
        )
        return chatEntity(chat)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


"""
    Get User Chat Messages
"""

async def get_user_chat_messages(chat_id: str, user_id: str):
    try:
        existing_chat = await chat_collection().find_one(
            {"_id": ObjectId(chat_id), "user_id": user_id}
        )
        # print("Existing chat found:", existing_chat)
        if not existing_chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        messages = (
            await message_collection().find({"chat_id": chat_id}).to_list(length=100)
        )

        # print("Retrieved messages:", messages)
        return messageListEntity(messages)
       
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



"""
    Delete User Chat
"""


async def delete_user_chat(chat_id: str, user_id: str):
    try:
        existing_chat = await chat_collection().find_one(
            {"_id": ObjectId(chat_id), "user_id": user_id}
        )
        if not existing_chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        result = await chat_collection().delete_one(
            {"_id": ObjectId(chat_id), "user_id": user_id}
        )
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Chat not found")
        return chatEntity(existing_chat)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


"""
    Send User Message
"""
async def send_user_message(chat_id: str, user_id: str, message: SendUserMessageRequest):
    try:
        # Check chat exists
        existing_chat = await chat_collection().find_one(
            {"_id": ObjectId(chat_id), "user_id": user_id}
        )
        if not existing_chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        # === STEP 1: Store user message with explicit timestamp ===
        user_message_timestamp = datetime.utcnow()
        request_message = Message(
            chat_id=chat_id,
            content=message.content,
            role=MessageRole.user,
            created_at=user_message_timestamp,
            updated_at=user_message_timestamp,
        )
        request_result = await message_collection().insert_one(request_message.model_dump())
        print(f'request result with inserted_id >>>>>>>> {request_result}')
        if not request_result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to send message")

        # Fetch last two conversation entries from user_query_collection
        user_queries = await user_query_collection().find(
            {"chat_id": chat_id}
        ).sort("created_at", -1).to_list(length=2)

        if not user_queries:
            expanded_query = message.content
            print(f'expanded_query without user_queries: {expanded_query}')
        else:
            conversation = [{"role": "user", "content": q["content"]} for q in user_queries]
            expanded_query = await expand_user_query(conversation, message.content, user_id)
            print(f'expanded_query with user_queries: {expanded_query}')

        # Store expanded query in user_query_collection
        expanded_message = Message(
            chat_id=chat_id,
            content=expanded_query,
            role=MessageRole.user,
            created_at=user_message_timestamp,
            updated_at=user_message_timestamp,
        )
        await user_query_collection().insert_one(expanded_message.model_dump())

        # === STEP 2: Call RAG pipeline (this takes time) ===
        from app.utils.pages_wise_metadata import processor
        rag_response = await processor.ask_question(user_id, expanded_message.content)

        ai_answer = rag_response.get("answer", "No answer found.")
        sources = rag_response.get("sources", [])

        # === STEP 3: Capture assistant response timestamp AFTER RAG completes ===
        assistant_message_timestamp = datetime.utcnow()
        
        # Store assistant response
        response_message = Message(
            chat_id=chat_id,
            content=ai_answer,
            sources=sources,
            role=MessageRole.assistant,
            created_at=assistant_message_timestamp,
            updated_at=assistant_message_timestamp,
        )
        response_result = await message_collection().insert_one(response_message.model_dump())
        if not response_result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to send message")

        # Store assistant response in user_query_collection
        assistant_message = Message(
            chat_id=chat_id,
            content=ai_answer.strip(),
            role=MessageRole.assistant,
            created_at=assistant_message_timestamp,
            updated_at=assistant_message_timestamp,
        )
        await user_query_collection().insert_one(assistant_message.model_dump())

        # Fetch both inserted messages
        request_message_db = await message_collection().find_one({"_id": request_result.inserted_id})
        response_message_db = await message_collection().find_one({"_id": response_result.inserted_id})

        return {
            "response_message": messageEntity(response_message_db),
            "request_message": messageEntity(request_message_db),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



"""
    Update User Chat
"""


async def update_user_chat(chat_id: str, chat: UpdateUserChatRequest, user_id: str):
    try:
        existing_chat = await chat_collection().find_one(
            {"_id": ObjectId(chat_id), "user_id": user_id}
        )
        if not existing_chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        result = await chat_collection().update_one(
            {"_id": ObjectId(chat_id), "user_id": user_id},
            {"$set": {"name": chat.name}},
        )
        chat = await chat_collection().find_one(
            {"_id": ObjectId(chat_id), "user_id": user_id}
        )
        return chatEntity(chat)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


"""
    Update User Message
"""


async def update_user_message(
    chat_id: str, message_id: str, data: UpdateUserMessageRequest, user_id: str
):
    try:
        existing_chat = await chat_collection().find_one(
            {"_id": ObjectId(chat_id), "user_id": user_id}
        )
        if not existing_chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        existing_message = await message_collection().find_one(
            {"_id": ObjectId(message_id), "chat_id": chat_id}
        )
        if not existing_message:
            raise HTTPException(status_code=404, detail="Message not found")

        await message_collection().update_one(
            {"_id": ObjectId(message_id), "chat_id": chat_id},
            {"$set": {"rating": data.rating}},
        )
        message = await message_collection().find_one(
            {"_id": ObjectId(message_id), "chat_id": chat_id}
        )

        # Update the chat with the new message
        question = sample_question_and_answer[0]
        ai_generated_response = open(question["answer_path"], "r").read()
        image_injected_response = inject_image_markdown(ai_generated_response)
        html_response = markdown.markdown(image_injected_response, extensions=["extra"])

        message["content"] = {
            "answer": html_response,
            "source": [
                {
                    "name": "page 1",
                    "content": html_response,
                },
                {
                    "name": "page 2",
                    "content": html_response,
                },
            ],
        }
        return messageEntity(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
    File Upload for User Chat
"""
# import aiofiles
from fastapi import UploadFile  
from typing import List
from app.models.organization_file_model import OrganizationFile
from app.serializers.organization_file_serializers import OrganizationFileEntity
from app.db.mongodb import organization_admin_collection, document_collection, get_fs , organization_user_collection 
from app.core.config import settings
from app.core.rabbitmq_client import rabbitmq_client  
import hashlib

async def user_file_upload(
    category_id: str, files: UploadFile, tags: List[str], user_id: str
):
    existing_org_admin = await organization_admin_collection().find_one(
        {"_id": ObjectId(user_id)}
    )
    if existing_org_admin:
        organization_id = existing_org_admin["organization_id"]
    else:
        existing_org_user = await organization_user_collection().find_one(
            {"_id": ObjectId(user_id)}
        )
        if not existing_org_user:
            raise HTTPException(status_code=404, detail="User not found")
        organization_id = existing_org_user["organization_id"]

    if category_id == "someCategoryId":
      category_id = existing_org_user["category_id"]
 
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="Files required")
    
    if not len(files) <= settings.MAX_FILES_PER_FOLDER:
        raise HTTPException(status_code=400, detail="10 files only allowed")
        
    processed_files = []
    rejected_files = []
    
    for file in files:
        content = await file.read()
        
        # validate the file size
        if len(content) > settings.MAX_FILE_SIZE:
            rejected_files.append({
                "filename": file.filename,
                "reason": f"File size exceeds {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB limit"
            })
            continue
        
        new_doc = {
            "organization_id": organization_id,
            "uploaded_by": user_id,
            "category_id": category_id,
            "filename": file.filename,
            "file_size": file.size,
            "mime_type": file.content_type,
            "file_id": None,
            "tags": tags or [],
            "hash_key": None,
            "source_type": "PRIVATE_DRIVE",
            "current_stage": None,
            "status_history": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        
        # insert into database
        doc_result = await document_collection().insert_one(
            new_doc
        )
        
        # update status
        update_data = {
            "$set": {
                "current_stage": "UPLOAD_JOB_QUEUED",
                "updated_at": datetime.now(),
            },
            "$push": {
                "status_history": {
                    "stage": "UPLOAD_JOB_QUEUED",
                    "status": "completed",
                    "timestamp": datetime.now(),
                    "error_message": None,
                    "retry_count": 0
                }
            }
        }

        await document_collection().update_one(
            {"_id": doc_result.inserted_id},
            update_data
        )
    
        # create the file hash
        hash_key = hashlib.sha256(content).hexdigest()
        
        # check if the file already exist for the organization
        is_duplicate = await document_collection().find_one({
            "hash_key": hash_key,
            "organization_id": organization_id,
            "current_stage": "COMPLETED"
        })
        
        # if duplicate reject the file
        if is_duplicate:
            await document_collection().update_one(
                {"_id": doc_result.inserted_id},
                {
                    "$set": {
                        "current_stage": "FILE_ALREADY_EXISTS_SKIPPED",
                        "updated_at": datetime.now(),
                    },
                    "$push": {
                        "status_history": {
                            "stage": "FILE_ALREADY_EXISTS_SKIPPED",
                            "status": "completed",
                            "timestamp": datetime.now(),
                            "error_message": None,
                            "retry_count": 0
                        }
                    }
                }
            )

            doc =  await document_collection().find_one(
                {"_id": doc_result.inserted_id}
            )
            processed_files.append(OrganizationFileEntity(doc))    
            continue

        await document_collection().update_one(
            {"_id": doc_result.inserted_id},
            {
                "$set": {
                    "current_stage": "RAW_FILE_UPLOAD_STARTED",
                    "updated_at": datetime.now(),
                    "hash_key": hash_key
                },
                "$push": {
                    "status_history": {
                        "stage": "RAW_FILE_UPLOAD_STARTED",
                        "status": "completed",
                        "timestamp": datetime.now(),
                        "error_message": None,
                        "retry_count": 0
                    }
                }
            }
        )
        
        grid_fs_id = await get_fs().upload_from_stream(
            new_doc["filename"],
            content,
            metadata={
                "type": new_doc["mime_type"],
                "organization_id": new_doc["organization_id"],
                "uploaded_by": user_id,
                "doc_id": str(doc_result.inserted_id),
                "doc_type": "RAW",
                "source": "PRIVATE_DRIVE",
                "uploaded_at": datetime.now()
            }
        )

        await document_collection().update_one(
            {"_id": doc_result.inserted_id},
            {
                "$set": {
                    "current_stage": "RAW_FILE_UPLOAD_UPLOADED",
                    "updated_at": datetime.now(),
                },
                "$push": {
                    "status_history": {
                        "stage": "RAW_FILE_UPLOAD_UPLOADED",
                        "status": "completed",
                        "timestamp": datetime.now(),
                        "error_message": None,
                        "retry_count": 0
                    }
                }
            }
        )
        
        rabbitmq_job = {
            "doc_id": str(doc_result.inserted_id),
            "user_id": user_id,
        }
                
        await rabbitmq_client.send_message(
            settings.MD_FILE_CONVERSION_QUEUE,
            json.dumps(rabbitmq_job)
        )

        await document_collection().update_one(
            {"_id": doc_result.inserted_id},
            {
                "$set": {
                    "current_stage": "MD_CONVERSION_JOB_QUEUED",
                    "updated_at": datetime.now(),
                },
                "$push": {
                    "status_history": {
                        "stage": "MD_CONVERSION_JOB_QUEUED",
                        "status": "completed",
                        "timestamp": datetime.now(),
                        "error_message": None,
                        "retry_count": 0
                    }
                }
            }
        )

        doc = await document_collection().find_one(
            {"_id": doc_result.inserted_id}
        )
        processed_files.append(OrganizationFileEntity(doc))
    
    return processed_files