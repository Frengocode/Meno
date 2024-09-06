from fastapi import APIRouter, Depends, WebSocket
from authentication.oauth import get_current_user
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import User
from database.schema import NotificationResponse
from services.api.v1.notification_service import NotificatiinService
from services.api.v1.chat_service import  manager

notification_router = APIRouter(tags=['Notification'])

@notification_router.websocket("/ws/notifications/")
async def websocket_endpoint(websocket: WebSocket, current_user: dict = Depends(get_current_user)):
    user_id = current_user.id
    await manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_text()
    except Exception as e:
        print(f"Ошибка WebSocket: {e}")
    finally:
        manager.disconnect(websocket, user_id)


@notification_router.get('/get-user-notifications/', response_model=list[NotificationResponse])
async def get_all_user_notifcations(session: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = NotificatiinService(session=session)
    return await service.get_all_user_notification(current_user=current_user)
