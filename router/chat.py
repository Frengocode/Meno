from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from database import database, models, schema
from authentication import oauth
from typing import List
from datetime import datetime
import uuid
import os
import logging

IMAGEDIR = 'media/images'

router = APIRouter(
    prefix='/chat',
    tags=['Chat']
)

connected_clients = {}

@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int):
    await websocket.accept()
    if chat_id not in connected_clients:
        connected_clients[chat_id] = []
    connected_clients[chat_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            logging.info(f"Received message from chat {chat_id}: {data}")
            for client in connected_clients[chat_id]:
                if client != websocket:
                    await client.send_text(data)
    except WebSocketDisconnect:
        connected_clients[chat_id].remove(websocket)
        if not connected_clients[chat_id]:
            del connected_clients[chat_id]


@router.post("/send/{chat_id}/", response_model=schema.Message)
async def send_message(
    chat_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth.get_current_user),
    img_file: UploadFile = File(None),
    message: str = Form(...)
):
    if img_file:
        img_file.filename = f"{uuid.uuid4()}.jpg"
        contents = await img_file.read()
        file_path = os.path.join(IMAGEDIR, img_file.filename)
        with open(file_path, 'wb') as f:
            f.write(contents)
    else:
        logging.info('img file is none')

    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    if current_user.id not in [participant.user_id for participant in chat.participants]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    new_message = models.Message(
        message=message,
        author_id=current_user.id,
        chat_id=chat_id,
        timestamp=datetime.utcnow(),
        img_file=img_file.filename if img_file else None
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    message_response = schema.Message(
        id=new_message.id,
        content=new_message.message,
        author_id=new_message.author_id,
        chat_id=new_message.chat_id,
        timestamp=str(new_message.timestamp),
        profile_photo=new_message.author.profile_photo,
        author=str(new_message.author.username),
    )

    if chat_id in connected_clients:
        for client in connected_clients[chat_id]:
            await client.send_json(message_response.dict())

    return message_response


@router.post("/send_content/{chat_id}/", response_model=schema.UserContentResponse)
async def send_content(
    chat_id: int,
    content_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth.get_current_user)
):
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    if current_user.id not in [participant.user_id for participant in chat.participants]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    user_content = models.UserContent(
        sender_id=current_user.id,
        content_id=content_id,
        chat_id=chat_id,
        created_at=datetime.utcnow()
    )
    
    db.add(user_content)
    db.commit()
    db.refresh(user_content)

    return schema.UserContentResponse(
        id=user_content.id,
        sender_id=user_content.sender_id,
        content_id=user_content.content_id,
        chat_id=user_content.chat_id,
        created_at=user_content.created_at
    )


@router.post("/", response_model=schema.Chat)
async def create_chat(
    chat: schema.ChatCreate, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth.get_current_user)
):
    existing_chat = db.query(models.Chat).filter(
        models.Chat.participants.any(models.ChatParticipant.user_id.in_(chat.participants))
    ).first()

    if existing_chat:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chat with these participants already exists")

    participants = db.query(models.User).filter(models.User.id.in_(chat.participants)).all()
    if not participants:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participants not found")

    if current_user not in participants:
        participants.append(current_user)

    new_chat = models.Chat()
    db.add(new_chat)
    db.flush()

    for participant in participants:
        db.add(models.ChatParticipant(chat_id=new_chat.id, user_id=participant.id))

    db.commit()
    db.refresh(new_chat)

    participants_info = [
        schema.ChatParticipant(
            id=participant.id,
            username=participant.username,
            user_id=participant.id,
            profile_photo=participant.profile_photo
        )
        for participant in participants
    ]

    return schema.Chat(
        id=new_chat.id,
        participants=participants_info,
        messages=[]
    )


@router.get("/get_user_chat/{chat_id}", response_model=schema.Chat)
async def get_chat(
    chat_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth.get_current_user)
):
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    if current_user.id not in [participant.user_id for participant in chat.participants]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    messages = [
        schema.Message(
            id=message.id,
            content=message.message,
            profile_photo=message.author.profile_photo,
            img_file=message.img_file,
            author_id=message.author_id,
            chat_id=message.chat_id,
            timestamp=message.timestamp,
            author=str(message.author.username),
        ) for message in chat.messages
    ]

    participants = [
        schema.ChatParticipant(
            id=p.user_id,
            username=p.user.username,
            user_id=p.user.id,
            profile_photo=p.user.profile_photo,
        ) for p in chat.participants
    ]

    user_contents = db.query(models.UserContent).filter(models.UserContent.chat_id == chat_id).all()
    contents = [
        schema.Content(
            id=user_content.content.id,
            author_id=user_content.sender_id,
            timestamp=user_content.created_at,
            sender_username=user_content.sender.username,
            content_photo=user_content.content.content_photo,
            sender_profile_photo=user_content.sender.profile_photo,
        ) for user_content in user_contents
    ]

    return schema.Chat(
        id=chat.id,
        participants=participants,
        messages=messages,
        contents=contents
    )

@router.get("/my_chats", response_model=List[schema.Chat])
async def get_user_chats(
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth.get_current_user)
):
    user_chats = db.query(models.Chat).join(models.ChatParticipant).filter(
        models.ChatParticipant.user_id == current_user.id
    ).all()

    chat_list = []
    for chat in user_chats:
        participants_info = [
            schema.ChatParticipant(
                id=participant.user.id,
                username=participant.user.username,
                profile_photo=participant.user.profile_photo,
                user_id=participant.user.id,
            )
            for participant in chat.participants
        ]
        chat_list.append(schema.Chat(id=chat.id, participants=participants_info, contents=chat.user_content))

    return chat_list

# Удаление чата
@router.delete('/delete-chat/{chat_id}')
async def delete_chat(chat_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth.get_current_user)):
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    
    if not chat:
        logging.info(f"Chat with ID {chat_id} not found")
        raise HTTPException(status_code=404, detail='Chat not found')
    
    logging.info(f"Participants of chat {chat_id}: {[participant.user_id for participant in chat.participants]}")
    logging.info(f"Current user ID: {current_user.id}")
    
    is_participant = any(participant.user_id == current_user.id for participant in chat.participants)
    
    if not is_participant:
        logging.warning(f"User {current_user.id} is not a participant of chat {chat_id}")
        raise HTTPException(status_code=403, detail='Access denied')
    
    db.delete(chat)
    db.commit()
    
    logging.info(f"Chat {chat_id} successfully deleted")
    return {"detail": f"Chat {chat_id} successfully deleted"}
