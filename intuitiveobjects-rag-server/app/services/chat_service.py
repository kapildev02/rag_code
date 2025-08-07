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
from app.serializers.message_serializers import messageListEntity, messageEntity
from bson.objectid import ObjectId
from app.utils.functions import inject_image_markdown
from app.utils.response_generator import generate_ai_response
import markdown
from app.data.questions import sample_question_and_answer

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
        if not existing_chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        messages = (
            await message_collection().find({"chat_id": chat_id}).to_list(length=100)
        )

        response_messages = []
        for message in messages:
            if message["role"] == MessageRole.assistant:
                response_messages.append(messageEntity(message))
            else:
                question = sample_question_and_answer[0]
                ai_generated_response = open(question["answer_path"], "r").read()
                image_injected_response = inject_image_markdown(ai_generated_response)
                html_response = markdown.markdown(
                    image_injected_response, extensions=["extra"]
                )

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
                response_messages.append(messageEntity(message))

        return response_messages
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
async def send_user_message(
    chat_id: str, user_id: str, message: SendUserMessageRequest
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

        # Call your RAG pipeline here!
        from app.utils.pages_wise_metadata import processor  # import here or at top
        rag_response = await processor.ask_question(message.content)

        # Format the answer and sources
        answer = rag_response.get("answer", "No answer found.")
        response_message = Message(
            chat_id=chat_id,
            content= answer.strip(),  # Assuming answer is a string
            role=MessageRole.assistant,
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

        response_message_doc = await message_collection().find_one(
            {"_id": response_message_result.inserted_id}
        )
        request_message_doc = await message_collection().find_one(
            {"_id": request_message_result.inserted_id}
        )

        return {
            "response_message": messageEntity(response_message_doc),
            "request_message": messageEntity(request_message_doc),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# async def send_user_message(
#     chat_id: str, user_id: str, message: SendUserMessageRequest
# ):
#     try:
#         existing_chat = await chat_collection().find_one(
#             {"_id": ObjectId(chat_id), "user_id": user_id}
#         )
#         if not existing_chat:
#             raise HTTPException(status_code=404, detail="Chat not found")

#         request_message = Message(
#             chat_id=chat_id, content=message.content, role=MessageRole.user
#         )

#         ai_response = generate_ai_response(message.content)

#         response_message = Message(
#             chat_id=chat_id, content=ai_response, role=MessageRole.assistant
#         )

#         request_message_result = await message_collection().insert_one(
#             request_message.model_dump()
#         )

#         if request_message_result.inserted_id is None:
#             raise HTTPException(status_code=500, detail="Failed to send message")

#         response_message_result = await message_collection().insert_one(
#             response_message.model_dump()
#         )

#         if response_message_result.inserted_id is None:
#             raise HTTPException(status_code=500, detail="Failed to send message")

#         response_message = await message_collection().find_one(
#             {"_id": response_message_result.inserted_id}
#         )
#         request_message = await message_collection().find_one(
#             {"_id": request_message_result.inserted_id}
#         )

#         # Update the chat with the new message
#         question = sample_question_and_answer[0]
#         ai_generated_response = open(question["answer_path"], "r").read()
#         image_injected_response = inject_image_markdown(ai_generated_response)
#         html_response = markdown.markdown(image_injected_response, extensions=["extra"])

#         response_message["content"] = {
#             "answer": html_response,
#             "source": [
#                 {
#                     "name": "page 1",
#                     "content": html_response,
#                 },
#                 {
#                     "name": "page 2",
#                     "content": html_response,
#                 },
#             ],
#         }

#         return {
#             "response_message": messageEntity(response_message),
#             "request_message": messageEntity(request_message),
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


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
