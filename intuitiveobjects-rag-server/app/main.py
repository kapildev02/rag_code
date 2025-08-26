from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.db.mongodb import connect_to_mongodb, close_mongodb_connection
from app.api.v1.routes import router as v1_router
from app.api.v2.routes import router as v2_router
from app.core.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
)
from contextlib import asynccontextmanager
from app.core.rabbitmq_client import rabbitmq_client
import socketio
from collections import defaultdict
from app.core.config import settings
import aio_pika
import json
from app.serializers.organization_file_serializers import OrganizationFileEntity
from app.utils.auth import get_current_user
from app.db.mongodb import organization_file_collection,document_collection, close_mongodb_connection
from bson import ObjectId
from fastapi.encoders import jsonable_encoder



connected_clients = defaultdict(set)

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

async def document_notify(user_id: str, data: dict):
    """
    Notify connected clients about a document-related event.
    """
    doc_id = data.get("doc_id")

    file = await document_collection().find_one({"_id": ObjectId(doc_id)})

    if not file:
        # Optionally log or handle the missing file case
        return

    organization_file = OrganizationFileEntity(file)
    
    if not user_id or user_id not in connected_clients:
        return

    for sid in connected_clients[user_id]:
        await sio.emit("document_notify", jsonable_encoder(organization_file), to=sid)


async def on_message(message: aio_pika.IncomingMessage):    
    # decode the message body
    data = json.loads(message.body.decode())
    
    # get user_id from the message data
    user_id = data.get("user_id")
    
    print(f"User ID: {user_id}")
    
    if not user_id:
        await message.ack()
        
    match data.get("event_type"):
        case "document_notify":
            await document_notify(user_id, data)
        case _:
            return "Something else"
        
    for sid in connected_clients[user_id]:
        await sio.emit("message", data, to=sid)
    await message.ack()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongodb()
    await rabbitmq_client.connect()
    await rabbitmq_client.consume_message(settings.NOTIFY_QUEUE, on_message)
    yield
    await close_mongodb_connection()

app = FastAPI(
    title="Demo API",
    description="This is a Demo API for testing purposes",
    version="1.0.0",
    lifespan=lifespan
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# Setup exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Setup MongoDB connection events

app.add_event_handler("startup", connect_to_mongodb)
app.add_event_handler("shutdown", close_mongodb_connection)

# Include API routes
app.include_router(v1_router, prefix="/api/v1")
app.include_router(v2_router, prefix="/api/v2")


@app.get("/")
async def root():
    return {"message": "Welcome to Demo API with MongoDB"}


@sio.event
async def connect(sid, environ, auth):
    print(f"Client connected: {sid} and auth: {auth}")
    try:
        token = auth.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized")
        auth_data = get_current_user(token)
        print(f"Client connected: {sid} with user_id: {auth_data.user_id}")
        connected_clients[auth_data.user_id].add(sid)
    except Exception as e:
        print(f"Error connecting client: {e}")
        await sio.emit("error", "Unauthorized")
        await sio.disconnect(sid)


@sio.event
async def disconnect(sid):
    for user_id, sids in connected_clients.items():
        if sid in sids:
            sids.remove(sid)
            print(f"Client disconnected: {sid} for user_id: {user_id}")
            break
    print(f"Client disconnected: {sid}")
