from fastapi import (
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
from database import models, schema
from authentication import oauth
from datetime import datetime
import uuid
import os
import logging
import json
from sqlalchemy import or_


IMAGEDIR = "media/images"

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, chat_id: int):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []
        self.active_connections[chat_id].append(websocket)

    async def send_notification(self, user_id: int, notification: dict):
        # Преобразуем timestamp в isoformat для JSON

        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_json(notification)

    def disconnect(self, websocket: WebSocket, chat_id: int):
        if chat_id in self.active_connections:
            self.active_connections[chat_id].remove(websocket)
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]

    async def broadcast(self, chat_id: int, message: dict):
        if chat_id in self.active_connections:
            if "timestamp" in message and isinstance(message["timestamp"], datetime):
                message["timestamp"] = message["timestamp"].isoformat()

            for connection in self.active_connections[chat_id]:
                    await connection.send_json(message)



manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, chat_id: int):
    await manager.connect(websocket, chat_id)

    try:
        while True:
            data = await websocket.receive_text()

            message_data = json.loads(data)

            if "timestamp" in message_data and isinstance(
                message_data["timestamp"], datetime
            ):
                message_data["timestamp"] = message_data["timestamp"].isoformat()

            message_data["author"] = message_data.get("author", "Unknown")
            message_data["profile_photo"] = message_data.get("profile_photo", None)

            await manager.broadcast(chat_id, message_data)
    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id)



class ChatService:
    def __init__(self, session: Session):
        self.session = session

    async def send_message(
        self,
        chat_id: int,
        current_user: models.User,
        img_file: UploadFile = File(None),
        message: str = Form(...),
    ):
        img_filename = None
        if img_file:
            img_filename = f"{uuid.uuid4()}.jpg"
            contents = await img_file.read()
            file_path = os.path.join(IMAGEDIR, img_filename)
            with open(file_path, "wb") as f:
                f.write(contents)

        chat = self.session.query(models.Chat).filter(models.Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
            )

        if current_user.id not in [
            participant.user_id for participant in chat.participants
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        # Создание нового сообщения
        new_message = models.Message(
            message=message,
            author_id=current_user.id,
            chat_id=chat_id,
            timestamp=datetime.utcnow(),
            img_file=img_filename,
        )

        # Создание уведомления для всех пользователей, кроме автора сообщения

        self.session.add(new_message)
        self.session.commit()
        self.session.refresh(new_message)

        # Формирование ответа на сообщение
        message_response = schema.Message(
            id=new_message.id,
            content=new_message.message,
            author_id=new_message.author_id,
            chat_id=new_message.chat_id,
            timestamp=str(new_message.timestamp),
            profile_photo=new_message.author.profile_photo,
            author=str(new_message.author.username),
            img_file=new_message.img_file,
        )

        await manager.broadcast(chat_id, message_response.dict())

        return message_response

    async def send_content(
        self,
        request: schema.SendContentSchema,
        current_user: models.User,
    ):
        chat = (
            self.session.query(models.Chat)
            .filter(models.Chat.id == request.chat_id)
            .first()
        )
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
            )

        content = (
            self.session.query(models.Content)
            .filter(models.Content.id == request.content_id)
            .filter(
                or_(
                    models.Content.is_archived != True,
                    models.Content.is_archived == None,
                )
            )
            .first()
        )
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        if current_user.id not in [
            participant.user_id for participant in chat.participants
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        user_content = models.UserContent(
            sender_id=current_user.id,
            content_id=request.content_id,
            chat_id=request.chat_id,
            created_at=datetime.utcnow(),

            message_for_sending_content = request.message_for_sending_content if request.message_for_sending_content else None,
            
        )

        self.session.add(user_content)
        self.session.commit()
        self.session.refresh(user_content)

        response = schema.UserContentResponse(
            id=user_content.id,
            sender_id=user_content.sender_id,
            content_id=user_content.content_id,
            chat_id=user_content.chat_id,
            created_at=user_content.created_at,
            message_for_sending_content = user_content.message_for_sending_content if user_content.message_for_sending_content else None
        
        )

        await manager.broadcast(request.chat_id, response.dict())

        return response

    async def create_chat(
        self,
        chat: schema.ChatCreate,
        current_user: models.User,
    ):
        existing_chat = (
            self.session.query(models.Chat)
            .filter(
                models.Chat.participants.any(
                    models.ChatParticipant.user_id.in_(chat.participants)
                )
            )
            .first()
        )

        if existing_chat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chat with these participants already exists",
            )

        participants = (
            self.session.query(models.User)
            .filter(models.User.id.in_(chat.participants))
            .all()
        )
        if not participants:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Participants not found"
            )

        if current_user not in participants:
            participants.append(current_user)

        new_chat = models.Chat()
        self.session.add(new_chat)
        self.session.flush()

        for participant in participants:
            self.session.add(
                models.ChatParticipant(chat_id=new_chat.id, user_id=participant.id)
            )

        self.session.commit()
        self.session.refresh(new_chat)

        participants_info = [
            schema.ChatParticipant(
                user=schema.UserShema(
                    id=participant.id,
                    username=participant.username,
                    profile_photo=participant.profile_photo,
                )
            )
            for participant in participants
        ]

        return schema.Chat(id=new_chat.id, participants=participants_info, messages=[])

    async def get_chat(
        self,
        chat_id: int,
        current_user: models.User = Depends(oauth.get_current_user),
    ):
        chat = self.session.query(models.Chat).filter(models.Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
            )

        if current_user.id not in [
            participant.user_id for participant in chat.participants
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

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
            )
            for message in chat.messages
        ]

        participants = [
            schema.ChatParticipant(
                user=schema.UserShema(
                    id=p.user_id,
                    username=p.user.username,
                    profile_photo=p.user.profile_photo,
                )
            )
            for p in chat.participants
        ]

        user_contents = (
            self.session.query(models.UserContent)
            .join(models.Content, models.UserContent.content_id == models.Content.id)
            .filter(models.UserContent.chat_id == chat_id)
            .filter(
                or_(
                    models.Content.is_archived.is_(False),
                    models.Content.is_archived.is_(None),
                )
            )
            .order_by(models.UserContent.created_at.desc())
            .all()
        )

        contents = [
            schema.Content(
                id=user_content.content.id,
                author_id=user_content.sender_id,
                timestamp=user_content.created_at,
                content_creator_username=user_content.content.author.username,
                content_creator_profile_photo=user_content.content.author.profile_photo,
                sender_username=user_content.sender.username,
                content_photo=user_content.content.content_photo,
                sender_profile_photo=user_content.sender.profile_photo,
                sender_id=user_content.sender_id,

                message_sending_content = user_content.message_for_sending_content,
                user_content_id = user_content.id
            )
            for user_content in user_contents
        ]

        user_reels = (
            self.session.query(models.UserContent)
            .join(models.Reels, models.UserContent.reels_id == models.Reels.id)
            .filter(models.UserContent.chat_id == chat_id)
            .filter(
                or_(
                    models.Reels.is_archived.is_(False),
                    models.Reels.is_archived.is_(None),
                )
            )
            .order_by(models.UserContent.created_at.desc())
            .all()
        )

        video_reels = [
            schema.VideoReelsSchema(
                id=reels.reels.id,
                video_reels=str(reels.reels.video_reels),
                user=schema.UserShema(
                    id=reels.reels.user.id,
                    username=str(reels.reels.user.username),
                    profile_photo=str(reels.reels.user.profile_photo),
                ),
                sender_id=reels.sender_id,
                sender_profile_photo=str(reels.sender.profile_photo),
                sender_username=str(reels.sender.username),
                reels_title=reels.reels.reels_title,
                created_at=reels.reels.created_at,
                view_count=reels.reels.view_count,
                message_sended_content = reels.message_for_sending_content if reels.message_for_sending_content else None,
                
                user_content_id = reels.id
            )
            for reels in user_reels
        ]

        users = (
            self.session.query(models.UserContent)
            .join(models.User, models.UserContent.users_id == models.User.id)
            .filter(models.UserContent.chat_id == chat_id)
            .all()
        )

        users_response = [
            schema.UserShema(
                id=user.users.id,
                profile_photo=str(user.users.profile_photo),
                username=str(user.users.username),
                sender_profile_photo=str(user.sender.profile_photo),
                sender_username=str(user.sender.username),
                user_content_id = user.id
            )
            for user in users
        ]

        return schema.Chat(
            id=chat.id,
            participants=participants,
            messages=messages,
            contents=contents,
            reels=video_reels,
            users=users_response,
        )

    async def delete_chat(
        self,
        chat_id: int,
        current_user: models.User,
    ):
        chat = self.session.query(models.Chat).filter(models.Chat.id == chat_id).first()

        if not chat:
            logging.info(f"Chat with ID {chat_id} not found")
            raise HTTPException(status_code=404, detail="Chat not found")

        if current_user.id not in [p.user_id for p in chat.participants]:
            logging.info(
                f"User {current_user.id} not authorized to delete chat {chat_id}"
            )
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this chat"
            )

        self.session.delete(chat)
        self.session.commit()

        logging.info(f"Chat with ID {chat_id} successfully deleted")
        return {"detail": "Chat deleted successfully"}

    async def get_user_chats(
        self,
        current_user: models.User,
    ):
        user_chats = (
            self.session.query(models.Chat)
            .join(models.ChatParticipant)
            .filter(models.ChatParticipant.user_id == current_user.id)
            .all()
        )

        chat_list = []
        for chat in user_chats:

            participants_info = [
                schema.ChatParticipant(
                    user=schema.UserShema(
                        id=participant.user.id,
                        username=participant.user.username,
                        profile_photo=participant.user.profile_photo,
                    )
                )
                for participant in chat.participants
            ]

            chat_list.append(
                schema.Chat(
                    id=chat.id,
                    participants=participants_info,
                    contents=chat.user_content,
                )
            )

        return chat_list

    async def delete_message(
        self,
        message_id: int,
        current_user: models.User,
    ):

        message = (
            self.session.query(models.Message)
            .filter(models.Message.id == message_id)
            .first()
        )
        if not message:
            raise HTTPException(detail="Message Not found", status_code=404)

        if message.author_id == current_user.id:

            self.session.delete(message)
            self.session.commit()
            return "Message Deleted Succsesfully"

        else:
            raise HTTPException(detail="Message Author error", status_code=401)

    async def delete_any_type_content(
        self,
        content_id: int,
        current_user: models.User,
    ):

        content = (
            self.session.query(models.UserContent)
            .filter(models.UserContent.id == content_id)
            .filter(models.UserContent.sender_id == current_user.id)
            .first()
        )

        if not content:
            raise HTTPException(detail="Not Found", status_code=404)

        self.session.delete(content)
        self.session.commit()

        return "Deleted Succsesfully"

    async def send_reels(
        self,
        request: schema.SendReelsSchema,
        current_user: models.User,
    ):
        chat = (
            self.session.query(models.Chat)
            .filter(models.Chat.id == request.chat_id)
            .first()
        )
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
            )

        content = (
            self.session.query(models.Reels)
            .filter(models.Reels.id == request.reels_id)
            .filter(
                or_(models.Reels.is_archived != True, models.Reels.is_archived == None)
            )
            .first()
        )
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        if current_user.id not in [
            participant.user_id for participant in chat.participants
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        user_content = models.UserContent(
            sender_id=current_user.id,
            reels_id=request.reels_id,
            chat_id=request.chat_id,
            created_at=datetime.utcnow(),
            message_for_sending_content = request.message_for_sending_content if request.message_for_sending_content else None
        )

        self.session.add(user_content)
        self.session.commit()
        self.session.refresh(user_content)

        response = schema.UserContentResponse(
            id=user_content.id,
            sender_id=user_content.sender_id,
            content_id=user_content.reels_id,
            chat_id=user_content.chat_id,
            created_at=user_content.created_at,
            message_for_sending_content = user_content.message_for_sending_content if user_content.message_for_sending_content else None
        )

        await manager.broadcast(request.chat_id, response.dict())

        return response

    async def send_user(
        self,
        request: schema.SendUserSchema,
        current_user: models.User,
    ):
        chat = (
            self.session.query(models.Chat)
            .filter(models.Chat.id == request.chat_id)
            .first()
        )
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
            )

        content = (
            self.session.query(models.User)
            .filter(models.User.id == request.user_id)
            .first()
        )
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        if current_user.id not in [
            participant.user_id for participant in chat.participants
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        user_content = models.UserContent(
            sender_id=current_user.id,
            users_id=request.user_id,
            chat_id=request.chat_id,
            created_at=datetime.utcnow(),
        )

        self.session.add(user_content)
        self.session.commit()
        self.session.refresh(user_content)

        response = schema.UserContentResponse(
            id=user_content.id,
            sender_id=user_content.sender_id,
            content_id=user_content.users_id,
            chat_id=user_content.chat_id,
            created_at=user_content.created_at,
        )
        
        await manager.broadcast(request.chat_id, response.dict())

        return response


   