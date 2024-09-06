from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
    File,
    UploadFile,
    Form,
)
from sqlalchemy.orm import Session
from database import database, models, schema
from authentication import oauth
from typing import List
from datetime import datetime
import uuid
import os
import logging
import json
from sqlalchemy import or_
from services.api.v1.chat_service import websocket_endpoint, ChatService

IMAGEDIR = "media/images"

router = APIRouter(tags=["Chat"])


@router.websocket("/ws/{chat_id}")
async def websocket_connect(websocket: WebSocket, chat_id: int):
    return await websocket_endpoint(websocket=websocket, chat_id=chat_id)


@router.post("/send/{chat_id}/", response_model=schema.Message)
async def send_message(
    chat_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth.get_current_user),
    img_file: UploadFile = File(None),
    message: str = Form(...),
):

    service = ChatService(session=db)

    return await service.send_message(
        chat_id=chat_id, message=message, current_user=current_user, img_file=img_file
    )


@router.post("/send_content/{chat_id}/", response_model=schema.UserContentResponse)
async def send_content(
    request: schema.SendContentSchema,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth.get_current_user),
):
    service = ChatService(session=db)

    return await service.send_content(request=request, current_user=current_user)


@router.post("/create-chat/", response_model=schema.Chat)
async def create_chat(
    chat: schema.ChatCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth.get_current_user),
):
    service = ChatService(session=db)

    return await service.create_chat(chat=chat, current_user=current_user)


@router.get("/get_user_chat/{chat_id}", response_model=schema.Chat)
async def get_chat(
    chat_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth.get_current_user),
):
    service = ChatService(session=db)

    return await service.get_chat(chat_id=chat_id, current_user=current_user)


@router.delete("/delete-chat/{chat_id}")
async def delete_chat(
    chat_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth.get_current_user),
):
    service = ChatService(session=db)

    return await service.delete_chat(chat_id=chat_id, current_user=current_user)


@router.get("/my_chats/", response_model=List[schema.Chat])
async def get_user_chats(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth.get_current_user),
):
    service = ChatService(session=db)

    return await service.get_user_chats(current_user=current_user)


@router.delete("/message-delete/{message_id}/")
async def delete_message(
    message_id: int,
    session: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth.get_current_user),
):

    service = ChatService(session=session)

    return await service.delete_message(
        current_user=current_user, message_id=message_id
    )


@router.post("/send_reels/{chat_id}/", response_model=schema.UserContentResponse)
async def send_reels(
    request: schema.SendReelsSchema,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth.get_current_user),
):
    service = ChatService(session=db)

    return await service.send_reels(request=request, current_user=current_user)


@router.post("/send_user/{chat_id}/", response_model=schema.UserContentResponse)
async def send_user(
    request: schema.SendUserSchema,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth.get_current_user),
):
    service = ChatService(session=db)

    return await service.send_user(request=request, current_user=current_user)


@router.delete('/deleting_content/{content_id}/')
async def delete_any_content(content_id: int, session: Session = Depends(database.get_db), current_user: models.User = Depends(oauth.get_current_user)):

    service = ChatService(session=session)
    return await service.delete_any_type_content(content_id=content_id, current_user=current_user)

