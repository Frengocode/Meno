from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import models, schema
from authentication.oauth import get_current_user
import os
import uuid
from datetime import timedelta, datetime

IMAGEDIR = "media/images/"

router = APIRouter(prefix="/History", tags=["History"])


class HistoryService:
    def __init__(self, session: Session):
        self.session = session

    async def create_history(
        self,
        current_user: models.User = Depends(get_current_user),
        file: UploadFile = File(...),
    ):

        file.filename = f"{uuid.uuid4()}.jpg"
        history = await file.read()

        file_path = os.path.join(IMAGEDIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(history)

        new_history_obj = models.History(
            content=file.filename,
            author_id=current_user.id,
            created_at=datetime.utcnow(),
            delete_at=datetime.utcnow() + timedelta(days=1),
        )

        self.session.add(new_history_obj)
        self.session.commit()

        return {"message": "Content created successfully", "content": new_history_obj}

    async def like_button(
        self, history_id: int, current_user: models.User = Depends(get_current_user)
    ):

        history_model = (
            self.session.query(models.History)
            .filter(models.History.id == history_id)
            .first()
        )

        if not history_model:
            raise HTTPException(detail="History Not found", status_code=404)

        if current_user in history_model.liked_by:
            history_model.liked_by.remove(current_user)

        else:
            history_model.liked_by.append(current_user)

        self.session.commit()
        self.session.refresh(current_user)
        self.session.refresh(history_model)
        return {"message": "Content liked/unliked successfully"}

    async def get_history_with_primary_key(
        self, id: int, current_user: models.User = Depends(get_current_user)
    ):

        detail = (
            self.session.query(models.History).filter(models.History.id == id).first()
        )

        if not detail:
            raise HTTPException(
                status_code=404, detail=f"Content with id {id} not found"
            )

        existing_view = (
            self.session.query(models.View)
            .filter(
                models.View.history_id == id, models.View.user_id == current_user.id
            )
            .first()
        )

        if not existing_view:

            new_view = models.View(
                history_id=id, user_id=current_user.id, viewed_at=datetime.utcnow()
            )

            self.session.add(new_view)

            detail.views_count = (detail.views_count or 0) + 1
            self.session.commit()
            self.session.refresh(new_view)

        like = detail.liked_by
        likes_count = len(like)

        who_viewed_response = schema.UserShema(
            id=detail.who_viewed.user_id,
            username=str(detail.who_viewed.user.username),
            profile_photo=str(detail.who_viewed.user.profile_photo),
        )

        who_liked_history = detail.who_liked

        who_liked = schema.UserShema(

            id = who_liked_history.id,
            username = str(who_liked_history.username),
            profile_photo = str(who_liked_history.profile_photo)

        ) if who_liked_history else None

        response_data = schema.HistoryResponse(
            id=detail.id,
            author=schema.UserShema(
                id=detail.author_id,
                username=str(detail.author.username),
                profile_photo=str(detail.author.profile_photo),
            ),
            created_at=detail.created_at,
            views_count=detail.views_count,
            like_count=likes_count,
            content=detail.content,
            who_viewed=who_viewed_response,
            who_liked = who_liked
        )

        return response_data

    async def delete_history(
        self, id: int, current_user: models.User = Depends(get_current_user)
    ):

        history_obj = (
            self.session.query(models.History).filter(models.History.id == id).first()
        )

        if not history_obj:
            raise HTTPException(detail="Not found", status_code=404)

        if current_user.id == history_obj.author_id:

            self.session.delete(history_obj)
            self.session.commit()

            return {"message": "History Deleted Succsesfully"}
