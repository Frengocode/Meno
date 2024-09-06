from fastapi import HTTPException
from sqlalchemy.orm import Session
from database import models
from database import schema


class NotificatiinService:
    def __init__(self, session: Session):
        self.session = session

    

    async def get_all_user_notification(self, current_user: models.User):
    # Получаем все уведомления для текущего пользователя, отсортированные по дате создания
        notifications = (
            self.session.query(models.Notification)
            .filter(models.Notification.user_id == current_user.id)
            .order_by(models.Notification.created_at.desc())
            .all()
        )

        # Если уведомлений нет, возвращаем пустой список
        if not notifications:
            return []

        # Список для хранения всех уведомлений
        response = []

        # Проходим по каждому уведомлению и создаем объект ответа
        for notification in notifications:
            # Проверяем, есть ли связанный контент
            content = notification.content
            sender = notification.sender
            video_reels = notification.video_reels


            # Создаем объект ответа для каждого уведомления
            notification_response = schema.NotificationResponse(
                id=notification.id,

                sender=schema.UserShema(
                    id=sender.id,
                    username=str(sender.username),
                    profile_photo=str(sender.profile_photo),
                ) if sender else None,

                content=schema.ContentSchema(
                    id=content.id,
                    content_photo=content.content_photo,
                    created_at=content.created_at,
                    content_title=content.content_title
                ) if content else None,

                video_reels = schema.VideoReelsSchema(

                    id = video_reels.id,
                    video_reels = video_reels.video_reels,
                    reels_title = video_reels.reels_title,
                    view_count = video_reels.view_count,
                    created_at = video_reels.created_at

                ) if video_reels else None,

                type=notification.type,
            )

            # Добавляем уведомление в список ответов
            response.append(notification_response)

        return response
