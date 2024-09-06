from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from sqlalchemy.orm import Session
from database.models import View, Reels, User
from authentication.oauth import get_current_user
from database.database import get_db
from database import schema, models
from datetime import datetime
import uuid, os
from typing import List
import logging
from sqlalchemy import or_


logger = logging.getLogger(__name__)


video_reels_router = APIRouter(tags=["Video Reels"])

MEDIA_ROOT = "media/reels/"


class VideoReelService:
    def __init__(self, session: Session):
        self.session = session

    async def create_video_reels(
        self,
        current_user: User,
        reels_title: str = Form(...),
        video_reels: UploadFile = File(...),
        place: str = Form(None),
    ):

        if not video_reels.filename.endswith(".mp4"):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file extension. Only .mp4 files are allowed.",
            )

        file_size = await video_reels.read()
        if len(file_size) <= 10:
            raise HTTPException(
                status_code=400, detail="File size must be greater than 10 bytes."
            )

        video_reels.filename = f"{uuid.uuid4()}.mp4"

        file_path = os.path.join(MEDIA_ROOT, video_reels.filename)
        with open(file_path, "wb") as f:
            f.write(file_size)

        new_video_reels_obj = Reels(
            reels_title=reels_title,
            video_reels=video_reels.filename,
            created_at=datetime.utcnow(),
            user_id=current_user.id,
            place=place if place else None,
        )

        self.session.add(new_video_reels_obj)
        self.session.commit()

        return {
            "detail": "Video reel created successfully",
            "reel": new_video_reels_obj,
        }

    async def get_reels(
        self,
        id: int,
        current_user: User,
    ) -> schema.VideoReelsSchema | None:

        video_reels = (
            self.session.query(Reels)
            .filter(Reels.id == id)
            .filter(or_(Reels.is_archived != True, Reels.is_archived == None))
            .first()
        )
        if not video_reels:
            raise HTTPException(detail="Not FOUND", status_code=404)

        existing_view = (
            self.session.query(View)
            .filter(View.reels_id == id, View.user_id == current_user.id)
            .first()
        )

        if not existing_view:
            new_view = View(
                reels_id=id, user_id=current_user.id, viewed_at=datetime.utcnow()
            )

            self.session.add(new_view)
            video_reels.view_count = (video_reels.view_count or 0) + 1

            self.session.commit()
            self.session.refresh(new_view)

        views_response = [
            schema.UserShema(
                id=video_reels.who_viewed.user_id,
                username=str(video_reels.who_viewed.user.username),
                profile_photo=str(video_reels.who_viewed.user.profile_photo),
            )
        ]

        if video_reels.who_liked is None:

            who_liked_response = None

        else:
            who_liked_response = schema.UserShema(
                id=video_reels.who_liked.id,
                username=str(video_reels.who_liked.username),
                profile_photo=str(video_reels.who_liked.profile_photo),
            )

        response = schema.VideoReelsSchema(
            id=video_reels.id,
            reels_title=video_reels.reels_title,
            video_reels=video_reels.video_reels,
            user=schema.UserShema(
                id=video_reels.user_id,
                username=str(video_reels.user.username),
                profile_photo=str(video_reels.user.profile_photo),
            ),
            place=video_reels.place,
            created_at=video_reels.created_at,
            view_count=video_reels.view_count,
            views_for_detail_page=views_response,
            like_count=len(video_reels.liked_by),
            who_liked=who_liked_response,
            is_archived=video_reels.is_archived,
        )

        return response

    async def get_all_reels(
        self,
        current_user: User,
    ):
        video_reels = (
            self.session.query(Reels)
            .filter(or_(Reels.is_archived != True, Reels.is_archived == None))
            .order_by(Reels.created_at.desc())  
            .all()
        )

        if not video_reels:
            raise HTTPException(detail="Not found", status_code=404)

        response = []

        for reels in video_reels:
            views_response = None
            who_liked_response = None

            if reels.who_viewed and reels.who_viewed.user:
                views_response = schema.UserShema(
                    id=reels.who_viewed.user.id,
                    username=str(reels.who_viewed.user.username),
                    profile_photo=str(reels.who_viewed.user.profile_photo),
                )

            if reels.who_liked:
                who_liked_response = schema.UserShema(
                    id=reels.who_liked.id,
                    username=str(reels.who_liked.username),
                    profile_photo=str(reels.who_liked.profile_photo),
                )

            response.append(
                schema.VideoReelsSchema(
                    id=reels.id,
                    reels_title=reels.reels_title,
                    video_reels=reels.video_reels,
                    user=schema.UserShema(
                        id=reels.user_id,
                        profile_photo=str(reels.user.profile_photo),
                        username=str(reels.user.username),
                    ),
                    place=reels.place,
                    created_at=reels.created_at,
                    view_count=reels.view_count,
                    like_count=len(reels.liked_by),
                    who_viewed=views_response,
                    who_liked=who_liked_response if who_liked_response else None,
                    shered_count=len(reels.user_reels),
                    is_archived=reels.is_archived,
                    commentarion_count=(
                        len(reels.comments) if reels.comments is not None else None
                    ),
                )
            )

        return response


    async def like_button(
        self,
        reels_id: int,
        current_user: User,
    ):

        reels = self.session.query(Reels).filter(Reels.id == reels_id).first()
        if not reels:
            raise HTTPException(detail="Not Found", status_code=404)

        if current_user not in reels.liked_by:
            reels.liked_by.append(current_user)

        else:
            reels.liked_by.remove(current_user)

            notification = models.Notification(
            user_id=reels.user_id, 
            sender_id=current_user.id,  
            video_reels_id=reels.id,
            type="like", 
        )

            self.session.add(notification)

        self.session.commit()
        self.session.refresh(current_user)
        self.session.refresh(reels)

        return {"message": {"detail": "Bro Likes was succsesfully"}}

    async def delete_reels(
        self,
        reels_id: int,
        current_user: User,
    ):

        reels = (
            self.session.query(Reels)
            .filter(Reels.id == reels_id)
            .filter(Reels.user_id == current_user.id)
            .first()
        )

        if not reels:
            logger.info("User Error Or Reels error")
            raise HTTPException(detail="Not Found", status_code=404)

        try:
            self.session.query(models.reels_likes).filter_by(reels_id=reels_id).delete()

            file_path = os.path.join(MEDIA_ROOT, str(reels.video_reels))
            os.remove(file_path)

            self.session.delete(reels)
            self.session.commit()

            logger.info("Deleted Successfully")
            return {"message": "Deleted Successfully"}

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error occurred during deletion: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def update_video_reels(
        self,
        reels_id: int,
        current_user: User,
        reels_title: str = Form(...),
        place: str = Form(None),
    ):

        reels = (
            self.session.query(Reels)
            .filter(Reels.id == reels_id)
            .filter(Reels.user_id == current_user.id)
            .first()
        )
        if not reels:
            raise HTTPException(detail="Not Found", status_code=404)

        reels.reels_title = reels_title
        reels.place = place

        self.session.commit()

        return {"detail": "Updated Succsesfully"}

    async def add_archive(
        self,
        reels_id: int,
        current_user: User,
    ):

        video_reels = (
            self.session.query(Reels)
            .filter(Reels.user_id == current_user.id)
            .filter(Reels.id == reels_id)
            .first()
        )
        if not video_reels:
            raise HTTPException(detail="Not Found", status_code=404)

        if video_reels.is_archived == True:
            video_reels.is_archived = False
            self.session.commit()
            return "Added to archive succsesfully"

        else:
            video_reels.is_archived = True
            self.session.commit()
            return "removed succsesfully"

    async def get_user_liked_reels(
        self,
        current_user: User,
    ):
        liked_reels_ids = (
            self.session.query(models.reels_likes.c.reels_id)
            .filter(models.reels_likes.c.user_id == current_user.id)
            .all()
        )

        if not liked_reels_ids:
            return []

        liked_reels = (
            self.session.query(Reels)
            .order_by(Reels.created_at.desc())
            .filter(Reels.id.in_([reels_id[0] for reels_id in liked_reels_ids]))
            .filter(or_(Reels.is_archived != True, Reels.is_archived == None))
            .all()
        )

        response = [
            schema.VideoReelsSchema(
                id=reels.id,
                video_reels=reels.video_reels,
                reels_title=reels.reels_title,
                user=schema.UserShema(
                    id=reels.id,
                    username=str(reels.user.username),
                    profile_photo=str(reels.user.profile_photo),
                ),
                like_count=len(reels.liked_by),
                view_count=reels.view_count,
                shered_count=len(reels.user_reels),
                created_at=reels.created_at,
            )
            for reels in liked_reels
        ]

        return response

    async def get_top_reels(
        self,
        current_user: User,
    ) -> List[schema.VideoReelsSchema]:

        top_reels = self.session.query(Reels).filter(Reels.view_count > 0).all()
        if not top_reels:
            raise HTTPException(detail="Not Found", status_code=404)

        response = []

        for reels in top_reels:
            views = [
                schema.UserShema(
                    id=view.user.id,
                    username=view.user.username,
                    profile_photo=view.user.profile_photo,
                    email=view.user.email,
                )
                for view in reels.views
                if view
            ]

            who_liked_response = [
                schema.UserShema(
                    id=who_liked.id,
                    username=who_liked.username,
                    profile_photo=who_liked.profile_photo,
                )
                for who_liked in reels.liked_by
                if who_liked
            ]

            response.append(
                schema.VideoReelsSchema(
                    id=reels.id,
                    video_reels=reels.video_reels,
                    reels_title=reels.reels_title,
                    created_at=reels.created_at,
                    user=schema.UserShema(
                        id=reels.user_id,
                        username=str(reels.user.username),
                        profile_photo=str(reels.user.profile_photo),
                    ),
                    view_count=reels.view_count,
                    like_count=len(reels.liked_by),
                    views_for_detail_page=views,
                    who_liked=who_liked_response,
                )
            )

        return response


