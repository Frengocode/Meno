from fastapi import Form, HTTPException
import json
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from database import models, schema


class CommentarionService:
    def __init__(self, session: Session):
        self.session = session

    async def create_commentarion(
        self, content_id: int, current_user: models.User, title: str = Form(...)
    ):

        content = (
            self.session.query(models.Content)
            .filter(models.Content.id == content_id)
            .first()
        )

        if content:

            new_commentarion_obj = models.CommentarionModel(
                title=title,
                user_id=int(current_user.id),
                date_pub=datetime.utcnow(),
                content=content,
            )

            self.session.add(new_commentarion_obj)
            self.session.commit()
            self.session.refresh(new_commentarion_obj)

            return new_commentarion_obj

        raise HTTPException(detail="Content Not Found", status_code=404)

    async def get_comments(
        self,
        content_id: int,
        current_user: models.User,
    ):

        content_model = (
            self.session.query(models.Content)
            .filter(models.Content.id == content_id)
            .first()
        )

        if not content_model:
            raise HTTPException(status_code=404, detail="Content not found")

        comments = (
            self.session.query(models.CommentarionModel)
            .filter(models.CommentarionModel.content_id == content_id)
            .order_by(models.CommentarionModel.date_pub.desc())
            .all()
        )

        if not comments:
            raise HTTPException(
                status_code=404, detail="No comments found for this content"
            )

        response = []
        for comment in comments:
            response.append(
                schema.CommentResponse(
                    id=comment.id,
                    content_id=comment.content_id,
                    user=str(comment.user.username),
                    title=str(comment.title),
                    user_id=comment.user_id,
                    date_pub=comment.date_pub,
                    profile_photo=str(comment.user.profile_photo),
                )
            )

        return response

    async def delete(self, id: int, current_user: models.User):

        comment = (
            self.session.query(models.CommentarionModel)
            .filter(models.CommentarionModel.user_id == current_user.id)
            .filter(models.CommentarionModel.id == id)
            .first()
        )

        if comment:

            self.session.delete(comment)
            self.session.commit()
            return "Comment Deleted Succsesfully"

        raise HTTPException(detail=f"Commentarion with {id} not found", status_code=404)

    async def create_comment_for_reels(
        self, reels_id: int, current_user: models.User, comment: str = Form(...)
    ):

        reels = (
            self.session.query(models.Reels).filter(models.Reels.id == reels_id).first()
        )
        if not reels:
            raise HTTPException(detail="Not Found", status_code=404)

        new_comment = models.CommentarionModel(
            title=comment,
            user_id=current_user.id,
            reels_id=reels.id,
            date_pub=datetime.utcnow(),
        )

        self.session.add(new_comment)
        self.session.commit()

        return new_comment

    async def get_comments_from_reels(
        self, reels_id: int, current_user: models.User
    ) -> List[schema.CommentResponse] | None:

        reels = (
            self.session.query(models.Reels).filter(models.Reels.id == reels_id).first()
        )
        if not reels:
            raise HTTPException(detail="Reels not found", status_code=404)

        comments = (
            self.session.query(models.CommentarionModel)
            .filter(models.CommentarionModel.reels_id == reels.id)
            .all()
        )
        if not comments:
            return []

        response = [
            schema.CommentResponse(
                id=comment.id,
                title=comment.title,
                user=str(comment.user.username),
                profile_photo=str(comment.user.profile_photo),
                user_id=comment.user_id,
                date_pub=comment.date_pub,
            )
            for comment in comments
        ]

        return response
