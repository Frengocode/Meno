from fastapi import HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
import os
import uuid
from datetime import datetime
from database import models, database, schema
from authentication.oauth import get_current_user
from typing import List
from sqlalchemy.sql import func
from sqlalchemy import or_
from PIL import Image
import io
from .chat_service import manager

IMAGEDIR = "media/images/"

class MenoService:
    def __init__(self, session: Session):
        self.session = session

    def compress_image_exact_size(
        self, image: Image, target_size_kb: int, output_path: str
    ):
        """Compress the image to exactly 50 KB, adjusting quality and resolution as needed."""
        quality = 85
        width, height = image.size

        while True:
            with io.BytesIO() as img_bytes:
                image.save(img_bytes, format="JPEG", quality=quality)
                size_kb = img_bytes.tell() / 1024

                if size_kb <= target_size_kb:
                    with open(output_path, "wb") as out_file:
                        out_file.write(img_bytes.getvalue())
                    break

            if size_kb > target_size_kb:
                width = int(width * 0.9)
                height = int(height * 0.9)
                image = image.resize((width, height), Image.Resampling.LANCZOS)

            quality -= 5

            if quality < 10 and size_kb > target_size_kb:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to compress image to 50 KB.",
                )

    async def create_content(
        self,
        current_user: models.User,
        content_title: str,
        file: UploadFile,
        content_for: schema.InteresingContentEnum,
    ):

        file.filename = f"{uuid.uuid4()}.jpg"

        image = Image.open(io.BytesIO(await file.read()))

        file_path = os.path.join(IMAGEDIR, file.filename)

        from starlette.concurrency import run_in_threadpool

        await run_in_threadpool(self.compress_image_exact_size, image, 50, file_path)

        new_content = models.Content(
            content_title=content_title,
            content_photo=file.filename,
            author_id=current_user.id,
            created_at=datetime.utcnow(),
            content_for=content_for,
        )

        self.session.add(new_content)
        self.session.commit()
        self.session.refresh(new_content)

        return {"message": "Content created successfully", "content": new_content}

    async def get_content_with_primary_key(self, id: int, current_user: models.User):

        detail = (
            self.session.query(models.Content)
            .filter(models.Content.id == id)
            .filter(
                or_(
                    models.Content.is_archived != True,
                    models.Content.is_archived == None,
                )
            )
            .first()
        )

        if not detail:
            raise HTTPException(
                detail=f"Content with id {id} not found", status_code=404
            )

        like = detail.liked_by
        like_count = len(like)

        comments_count = len(detail.commentarion)

        shered_count = len(detail.user_contents)

        existing_view = (
            self.session.query(models.View)
            .filter(
                models.View.content_id == id, models.View.user_id == current_user.id
            )
            .first()
        )

        if not existing_view:
            new_view = models.View(
                content_id=id, user_id=current_user.id, viewed_at=datetime.utcnow()
            )

            self.session.add(new_view)
            detail.view_count = (detail.view_count or 0) + 1
            self.session.commit()
            self.session.refresh(new_view)

        response_data = schema.ContentSchema(
            id=detail.id,
            content_title=detail.content_title,
            content_photo=detail.content_photo,
            author=schema.UserShema(
                id=detail.author.id,
                username=str(detail.author.username),
                profile_photo=str(detail.author.profile_photo),
            ),
            created_at=detail.created_at,
            view_count=detail.view_count,
            like_count=like_count,
            commentarion_count=comments_count,
            shered_counts=shered_count,
        )

        return response_data
    
    async def like_content(self, content_id: int, current_user: models.User):
        # Поиск контента по ID
        content = (
            self.session.query(models.Content)
            .filter(models.Content.id == content_id)
            .first()
        )

        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        # Проверка, лайкнул ли текущий пользователь контент
        if current_user in content.liked_by:
            content.liked_by.remove(current_user)
            action = "unliked"
        else:
            content.liked_by.append(current_user)
            action = "liked"

            notification = models.Notification(
                user_id=content.author_id, 
                sender_id=current_user.id,  
                content_id=content.id,
                type="like", 
            )

            self.session.add(notification)

            await manager.send_notification(notification.user_id, notification)


        self.session.commit()

        self.session.refresh(current_user)
        self.session.refresh(content)


        return {"message": f"Content {action} successfully"}


    async def add_user_chosen(self, id: int, current_user: models.User):

        content = (
            self.session.query(models.Content).filter(models.Content.id == id).first()
        )

        if not content:
            raise HTTPException(
                detail=f"Content With id {id} Not found", status_code=404
            )

        if current_user in content.user_chosen:
            content.user_chosen.remove(current_user)
            return "Added Succsesfully"

        else:
            content.user_chosen.append(current_user)

        self.session.commit()
        self.session.refresh(current_user)
        self.session.refresh(content)

        return {"detail": "Added/Removed"}

    async def get_popular_content(
        self,
        current_user: models.User,
    ):

        subquery = (
            self.session.query(
                models.content_likes.c.content_id,
                func.count(models.content_likes.c.user_id).label("like_count"),
            )
            .group_by(models.content_likes.c.content_id)
            .subquery()
        )

        popular_content_query = (
            self.session.query(models.Content, subquery.c.like_count)
            .join(subquery, models.Content.id == subquery.c.content_id)
            .order_by(models.Content.created_at.desc())
            .filter(subquery.c.like_count > 0)
            .filter(
                or_(
                    models.Content.is_archived != True,
                    models.Content.is_archived == None,
                )
            )
            .all()
        )

        if not popular_content_query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No popular content found"
            )

        response = []
        for content, like_count in popular_content_query:
            response.append(
                schema.ContentSchema(
                    id=content.id,
                    content_photo=content.content_photo,
                    content_title=content.content_title,
                    author=schema.UserShema(
                        id=content.author.id,
                        username=str(content.author.username),
                        profile_photo=str(content.author.profile_photo),
                    ),
                    profile_photo=content.author.profile_photo,
                    view_count=content.view_count,
                    created_at=content.created_at,
                    like_count=like_count,
                )
            )

        return response

    async def get_viewed_contents(
        self,
        current_user: models.User,
    ):

        viewed_content_ids = (
            self.session.query(models.View.content_id)
            .filter(models.View.user_id == current_user.id)
            .all()
        )

        if not viewed_content_ids:
            return []

        viewed_contents = (
            self.session.query(models.Content)
            .order_by(models.Content.created_at.desc())
            .filter(models.Content.id.in_([vc[0] for vc in viewed_content_ids]))
            .filter(
                or_(
                    models.Content.is_archived != True,
                    models.Content.is_archived == None,
                )
            )
            .all()
        )

        response_data = [
            schema.ContentSchema(
                id=content.id,
                content_title=content.content_title,
                content_photo=content.content_photo,
                author=schema.UserShema(
                    id=content.author_id,
                    username=str(content.author.username),
                    profile_photo=str(content.author.profile_photo),
                ),
                created_at=content.created_at,
                view_count=content.view_count,
            )
            for content in viewed_contents
        ]

        return response_data

    async def get_user_liked_contents(
        self,
        current_user: models.User,
    ):
        liked_content_ids = (
            self.session.query(models.content_likes.c.content_id)
            .filter(models.content_likes.c.user_id == current_user.id)
            .all()
        )

        if not liked_content_ids:
            return []

        liked_contents = (
            self.session.query(models.Content)
            .order_by(models.Content.created_at.desc())
            .filter(
                models.Content.id.in_(
                    [content_id[0] for content_id in liked_content_ids]
                )
            )
            .filter(
                or_(
                    models.Content.is_archived != True,
                    models.Content.is_archived == None,
                )
            )
            .all()
        )

        response_data = [
            schema.ContentSchema(
                id=content.id,
                content_title=content.content_title,
                content_photo=content.content_photo,
                author=schema.UserShema(
                    id=content.author_id,
                    username=str(content.author.username),
                    profile_photo=str(content.author.profile_photo),
                ),
                created_at=content.created_at,
                profile_photo=content.author.profile_photo,
                view_count=content.view_count,
            )
            for content in liked_contents
        ]

        return response_data

    async def get_all_publication(
        self,
        current_user: models.User,
    ):
        publications = (
            self.session.query(models.Content)
            .order_by(models.Content.created_at.desc())
            .filter(
                or_(
                    models.Content.is_archived != True,
                    models.Content.is_archived == None,
                )
            )
            .all()
        )

        response = []

        for content in publications:

            comments_count = (
                self.session.query(models.CommentarionModel)
                .filter(models.CommentarionModel.content_id == content.id)
                .count()
            )
            shered_counts = (
                self.session.query(models.UserContent)
                .filter(models.UserContent.content_id == content.id)
                .count()
            )

            response.append(
                schema.ContentSchema(
                    id=content.id,
                    author=schema.UserShema(
                        id=content.author.id,
                        username=str(content.author.username),
                        profile_photo=str(content.author.profile_photo),
                    ),
                    content_title=content.content_title,
                    created_at=content.created_at,
                    content_photo=content.content_photo,
                    view_count=content.view_count,
                    commentarion_count=comments_count,
                    shered_counts=shered_counts,
                    like_count=len(content.liked_by),
                )
            )

        return response

    async def delete(
        self,
        content_id: int,
        current_user: models.User,
    ):

        model = (
            self.session.query(models.Content)
            .filter(models.Content.id == content_id)
            .filter(models.Content.author_id == current_user.id)
            .first()
        )

        if not model:
            raise HTTPException(detail="Object not found", status_code=404)

        file_path = os.path.join(IMAGEDIR, str(model.content_photo))
        os.remove(file_path)

        self.session.delete(model)
        self.session.commit()

        return "Deleted Succsesfully"

    async def update_content(
        self,
        content_for: schema.InteresingContentEnum,
        current_user: models.User,
        id: int,
        content_title: str = Form(...),
    ):

        content = (
            self.session.query(models.Content).filter(models.Content.id == id).first()
        )

        if not content:
            raise HTTPException(
                detail=f"Content with id {id} not found", status_code=404
            )

        if current_user.id == content.author_id:

            content.content_title = content_title

            content.content_for = content_for if content_for else None

            self.session.commit()
            return "Content Updated Succsesfully"

    async def get_intering_contents(
        self,
        category: schema.InteresingContentEnum,
        current_user: models.User,
    ):

        category_value = category.value

        intersing_contens = (
            self.session.query(models.Content)
            .filter(models.Content.content_for == category_value)
            .filter(
                or_(
                    models.Content.is_archived != True,
                    models.Content.is_archived == None,
                )
            )
            .order_by(models.Content.created_at.desc())
            .all()
        )

        if not intersing_contens:
            raise HTTPException(detail="Not found", status_code=404)

        response = []
        for content in intersing_contens:
            comments_count = (
                self.session.query(models.CommentarionModel)
                .filter(models.CommentarionModel.content_id == content.id)
                .count()
            )
            shered_counts = (
                self.session.query(models.UserContent)
                .filter(models.UserContent.content_id == content.id)
                .count()
            )

            response.append(
                schema.ContentSchema(
                    id=content.id,
                    author=schema.UserShema(
                        id=content.author_id,
                        username=str(content.author.username),
                        profile_photo=str(content.author.profile_photo),
                    ),
                    content_title=content.content_title,
                    created_at=content.created_at,
                    content_photo=content.content_photo,
                    view_count=content.view_count,
                    profile_photo=content.author.profile_photo,
                    commentarion_count=comments_count,
                    shered_counts=shered_counts,
                )
            )

        return response

    async def add_content_to_archive(
        self,
        content_id: int,
        current_user: models.User,
    ):

        content = (
            self.session.query(models.Content)
            .filter(models.Content.id == content_id)
            .filter(models.Content.author_id == current_user.id)
            .first()
        )
        if not content:
            raise HTTPException(detail="Not Found", status_code=404)

        if content.is_archived == True:
            content.is_archived = False

            self.session.commit()

            return "Content removed from archive"

        else:
            content.is_archived = True

            self.session.commit()

            return {
                "detail": {
                    "message": f"Content with {content.id} id Succsesfully added to archive"
                }
            }

    async def get_all_archived_contents(
        self, current_user: models.User
    ) -> List[schema.ContentSchema] | None:

        archived_contents = (
            self.session.query(models.Content)
            .filter(models.Content.author_id == current_user.id)
            .filter(models.Content.is_archived == True)
            .all()
        )

        response = [
            schema.ContentSchema(
                id=archived_content.id,
                content_title=archived_content.content_title,
                content_photo=archived_content.content_photo,
                author=schema.UserShema(
                    id=archived_content.author_id,
                    username=str(archived_content.author.username),
                    profile_photo=str(archived_content.author.profile_photo),
                ),
                like_count=len(archived_content.liked_by),
                view_count=archived_content.view_count,
                shered_counts=len(archived_content.user_contents),
                commentarion_count=len(archived_content.commentarion),
                created_at=archived_content.created_at,
            )
            for archived_content in archived_contents
        ]

        return response

    async def get_likes_from_content(self, content_id: int, current_user: models.User):
        query = (
            self.session.query(models.User)
            .join(
                models.content_likes, models.content_likes.c.user_id == models.User.id
            )
            .filter(models.content_likes.c.content_id == content_id)
        )

        likes = query.all()

        if not likes:
            raise HTTPException(status_code=404, detail="Likes not found.")

        response = [
            schema.UserShemaForContent(
                id=like.id,
                profile_photo=like.profile_photo,
                username=like.username,
                email=like.email,
            )
            for like in likes
        ]

        return response
