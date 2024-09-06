from sqlalchemy.orm import Session
from database import models, schema
from authentication.hash import Hash
from fastapi import File, UploadFile, Form, HTTPException
import uuid
import os
from sqlalchemy import or_
from fastapi.responses import FileResponse
from typing import List

IMAGEDIR = "media/images/"


class UserService:

    def __init__(self, session: Session):
        self.session = session

    async def create_new_user(
        self,
        username: str = Form(...),
        password: str = Form(...),
        email: str = Form(...),
        file: UploadFile = File(...),
    ):

        file.filename = f"{uuid.uuid4()}.jpg"
        contents = await file.read()

        file_path = os.path.join(IMAGEDIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)

        exist_username = (
            self.session.query(models.User)
            .filter(models.User.username == username)
            .first()
        )
        if exist_username:
            raise HTTPException(detail=f"{username} already exists", status_code=400)

        if len(username) < 5:
            raise HTTPException(detail="Username too short", status_code=422)

        exist_email = (
            self.session.query(models.User).filter(models.User.email == email).first()
        )
        if exist_email:
            raise HTTPException(detail=f"{email} already exists", status_code=400)

        if not email.endswith("@gmail.com"):
            raise HTTPException(
                detail="Email must end with @gmail.com", status_code=400
            )

        if len(password) < 6:
            raise HTTPException(detail="Password too short", status_code=422)

        hashed_password = Hash.bcrypt(password)

        new_user = models.User(
            username=username,
            email=email,
            password=hashed_password,
            profile_photo=file.filename,
        )

        self.session.add(new_user)
        self.session.commit()
        self.session.refresh(new_user)

        return new_user

    async def get_user_with_id(
        self,
        user_id: int,
        current_user: models.User,
        content_category: schema.InteresingContentEnum,
    ):
        

        category_value = content_category.value

        user = self.session.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(detail="Not Found", status_code=404)

        contents = (
            self.session.query(models.Content)
            .filter(models.Content.author_id == user_id)
            .filter(
                or_(
                    models.Content.is_archived != True,
                    models.Content.is_archived == None,
                )
            )
            .order_by(models.Content.created_at.desc())
            .all()
        )

        get_content_by_category = (
            self.session.query(models.Content)
            .filter(models.Content.author_id == user_id)
            .filter(models.Content.content_for == category_value)
            .order_by(models.Content.created_at.desc())
            .all()
        )

        content_category_response = [
            schema.ContentSchema(
                id=category_content.id,
                author=schema.UserShema(
                    id=category_content.author.id,
                    username=str(category_content.author.username),
                    profile_photo=str(category_content.author.profile_photo),
                ),
                content_photo=category_content.content_photo,
                content_title=category_content.content_title,
                commentarion_count=len(category_content.commentarion),
                like_count=len(category_content.liked_by),
                view_count=category_content.view_count,
                created_at=category_content.created_at,
            )
            for category_content in get_content_by_category
        ]

        content_response = [
            schema.ContentSchema(
                id=content.id,
                content_title=content.content_title,
                content_photo=content.content_photo,
                author=schema.UserShema(
                    id=content.author_id,
                    username=str(content.author.username),
                    profile_photo=str(content.author.profile_photo),
                ),
                like_count=len(content.liked_by),
                commentarion_count=len(content.commentarion),
                created_at=content.created_at,
            )
            for content in contents
        ]

        user_histories = (
            self.session.query(models.History)
            .filter(models.History.author_id == user_id)
            .order_by(models.History.created_at.desc())
            .filter(
                or_(
                    models.Content.is_archived != True,
                    models.Content.is_archived == None,
                )
            )
            .all()
        )

        history_response = [
            schema.HistoryResponse(
                id=history.id,
                views_count=history.views_count,
                content=history.content,
                author=schema.UserShema(
                    id=history.author_id,
                    username=str(history.author.username),
                    profile_photo=str(history.author.profile_photo),
                ),
                created_at=history.created_at,
            )
            for history in user_histories
        ]

        video_reels = (
            self.session.query(models.Reels)
            .filter(models.Reels.user_id == user_id)
            .order_by(models.Reels.created_at.desc())
            .all()
        )

        video_reels_response = [
            schema.VideoReelsSchema(
                id=reels.id,
                video_reels=reels.video_reels,
                reels_title=reels.reels_title,
                user=schema.UserShema(
                    id=reels.user_id,
                    username=str(reels.user.username),
                    profile_photo=str(reels.user.profile_photo),
                ),
                like_count=len(reels.liked_by),
                created_at=reels.created_at,
                view_count=reels.view_count,
                place=reels.place,
            )
            for reels in video_reels
        ]

        who_followed_user_count = (
            self.session.query(models.User)
            .join(
                models.subscription, models.subscription.c.followed_id == models.User.id
            )
            .filter(models.subscription.c.follower_id == user_id)
            .count()
        )

        followers_user_count = (
            self.session.query(models.User)
            .join(
                models.subscription, models.subscription.c.follower_id == models.User.id
            )
            .filter(models.subscription.c.followed_id == user_id)
            .count()
        )

        user_response = schema.UserShemaForContent(
            id=user.id,
            profile_photo=user.profile_photo,
            username=user.username,
            is_closed=user.is_closed,
            email=user.email,
            name=user.name,
            surname=user.surname,
            biography=user.bigraph,
            followers_count=followers_user_count,
            who_followers_count=who_followed_user_count,
            content_count=len(video_reels_response) + len(content_response),
            content=content_response,
            reels=video_reels_response,
            history=history_response,
            get_content_with_category=content_category_response,
        )

        return user_response

    async def update_username(
        self,
        current_user: models.User,
        username: str = Form(...),
        surname: str = Form(None),
        name: str = Form(None),
        biography: str = Form(None),
        file: UploadFile = File(None)
    ):
        
        if file is not None:
            
        
            file.filename = f"{uuid.uuid4()}.jpg"
            contents = await file.read()

            file_path = os.path.join(IMAGEDIR, file.filename)
            with open(file_path, "wb") as f:
                f.write(contents)

        file_path = os.path.join(IMAGEDIR, str(current_user.profile_photo))
        os.remove(file_path)

        exist_username = (
            self.session.query(models.User)
            .filter(models.User.username == username)
            .first()
        )

        if exist_username:
            raise HTTPException(detail="Username already exists", status_code=409)

        current_user.username = username
        current_user.name = name
        current_user.surname = surname
        current_user.bigraph = biography
        current_user.profile_photo = file.filename if file.filename else None

        if len(username) < 4:
            raise HTTPException(detail="Username Most Small", status_code=402)

        self.session.commit()
        self.session.refresh(current_user)

        return schema.UserUpdateResponse(
            id=current_user.id,
            username=current_user.username,
            name=current_user.name,
            surname=current_user.surname,
            biography=current_user.bigraph,
            profile_photo = current_user.profile_photo
        )

    async def follow_user(self, user_id: int, current_user: models.User):

        if current_user.id == user_id:
            raise HTTPException(status_code=400, detail="You cannot follow yourself.")

        user_to_follow = (
            self.session.query(models.User).filter(models.User.id == user_id).first()
        )
        if not user_to_follow:
            raise HTTPException(status_code=404, detail="User not found.")

        if user_to_follow in current_user.followed_by:

            raise HTTPException(
                status_code=400, detail="You are already following this user."
            )

        current_user.followed_by.append(user_to_follow)
        self.session.commit()

        return {"message": "You have successfully followed the user."}

    async def unfollow(self, id: int, current_user: models.User):

        if current_user.id == id:
            raise HTTPException(status_code=400, detail="You cannot unfollow yourself.")

        user_to_unfollow = (
            self.session.query(models.User).filter(models.User.id == id).first()
        )
        if not user_to_unfollow:
            raise HTTPException(status_code=404, detail="User not found.")

        existing_subscription = self.session.execute(
            models.subscription.select().where(
                models.subscription.c.follower_id == current_user.id,
                models.subscription.c.followed_id == id,
            )
        ).fetchone()

        if existing_subscription:
            self.session.execute(
                models.subscription.delete().where(
                    models.subscription.c.follower_id == current_user.id,
                    models.subscription.c.followed_id == id,
                )
            )
            self.session.commit()
            return {"message": "Successfully unfollowed the user."}
        else:
            raise HTTPException(
                status_code=404, detail="You are not following this user."
            )

    async def get_subscribed_content(self, current_user: models.User):

        followed_ids = (
            self.session.query(models.subscription.c.followed_id)
            .filter(models.subscription.c.follower_id == current_user.id)
            .all()
        )

        followed_ids = [followed_id for (followed_id,) in followed_ids]

        if not followed_ids:
            raise HTTPException(status_code=404, detail="You are not following anyone")

        content = (
            self.session.query(models.Content)
            .filter(models.Content.author_id.in_(followed_ids))
            .filter(
                or_(
                    models.Content.is_archived != True,
                    models.Content.is_archived == None,
                )
            )
            .all()
        )

        if not content:
            raise HTTPException(
                status_code=404, detail="No content found from followed users"
            )

        content_response = []
        for item in content:
            author = (
                self.session.query(models.User)
                .filter(models.User.id == item.author_id)
                .first()
            )
            if not author:
                continue

            content_response.append(
                schema.ContentSchema(
                    id=item.id,
                    content_title=item.content_title,
                    content_photo=item.content_photo,
                    author=schema.UserShema(
                        id=item.author_id,
                        profile_photo=str(item.author.profile_photo),
                        username=str(item.author.username),
                    ),
                    created_at=item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    like_count=len(item.liked_by),
                    liked_by=[],
                    profile_photo=author.profile_photo,
                    view_count=item.view_count,
                    commentarion_count=len(item.commentarion),
                )
            )

            return content_response

    async def get_followers_users(self, user_id: int, current_user: models.User):

        following_users = (
            self.session.query(models.User)
            .join(
                models.subscription, models.subscription.c.followed_id == models.User.id
            )
            .filter(models.subscription.c.follower_id == user_id)
            .all()
        )

        if not following_users:
            raise HTTPException(status_code=404, detail="You are not following anyone")

        following_response = [
            schema.UserShemaForContent(
                id=user.id,
                email=user.email,
                username=user.username,
                profile_photo=user.profile_photo,
            )
            for user in following_users
        ]

        return following_response

    async def get_user_chosen_contents(self, current_user: models.User):
        chosen_content_ids = (
            self.session.query(models.chosen.c.content_id)
            .filter(models.chosen.c.user_id == current_user.id)
            .all()
        )

        if not chosen_content_ids:
            return []

        liked_contents = (
            self.session.query(models.Content)
            .filter(
                models.Content.id.in_(
                    [content_id[0] for content_id in chosen_content_ids]
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
                view_count=content.view_count,
            )
            for content in liked_contents
        ]

        return response_data

    async def search_users(
        self, current_user: models.User, username: str = None
    ) -> List[schema.UserShema]:

        if username:
            query = (
                self.session.query(models.User)
                .filter(models.User.username.ilike(f"%{username}%"))
                .all()
            )

        return query

    async def user_me(self, current_user: models.User):

        user_contents = (
            self.session.query(models.Content)
            .filter(models.Content.author_id == current_user.id)
            .order_by(models.Content.created_at.desc())
            .filter(
                or_(
                    models.Content.is_archived != True,
                    models.Content.is_archived == None,
                )
            )
            .all()
        )

        historys = (
            self.session.query(models.History)
            .filter(models.History.author_id == current_user.id)
            .order_by(models.History.created_at.desc())
            .all()
        )

        video_reels = (
            self.session.query(models.Reels)
            .filter(models.Reels.user_id == current_user.id)
            .filter(
                or_(models.Reels.is_archived != True, models.Reels.is_archived == None)
            )
            .order_by(models.Reels.created_at.desc())
            .all()
        )


        who_followed_user_count = (
            self.session.query(models.User)
            .join(
                models.subscription, models.subscription.c.followed_id == models.User.id
            )
            .filter(models.subscription.c.follower_id == current_user.id)
            .count()
        )

        followers_user_count = (
            self.session.query(models.User)
            .join(
                models.subscription, models.subscription.c.follower_id == models.User.id
            )
            .filter(models.subscription.c.followed_id == current_user.id)
            .count()
        )

        history_response = [
            schema.HistoryResponse(
                id=history.id,
                author=schema.UserShema(
                    id=history.author_id,
                    username=str(history.author.username),
                    profile_photo=str(history.author.profile_photo),
                ),
                created_at=history.created_at,
                like_count=len(history.liked_by),
                views_count=history.views_count,
                content=str(history.content),
            )
            for history in historys
        ]

        content_count = len(user_contents) + len(video_reels)
        followers_count = len(current_user.following)
        history_count = len(current_user.histories)

        content_response = [
            schema.ContentSchema(
                id=user_content.id,
                content_title=user_content.content_title,
                content_photo=user_content.content_photo,
                author=schema.UserShema(
                    id=user_content.author_id,
                    username=str(user_content.author.username),
                    profile_photo=str(user_content.author.profile_photo),
                ),
                created_at=user_content.created_at,
                profile_photo=str(user_content.author.profile_photo),
                like_count=len(user_content.liked_by),
                view_count=user_content.view_count,
            )
            for user_content in user_contents
        ]

        video_reels_response = [
            schema.VideoReelsSchema(
                id=reels.id,
                reels_title=reels.reels_title,
                video_reels=reels.video_reels,
                user=schema.UserShema(
                    id=reels.user.id,
                    username=str(reels.user.username),
                    profile_photo=str(reels.user.profile_photo),
                ),
                created_at=reels.created_at,
                like_count=len(reels.liked_by),
                view_count=reels.view_count,
            )
            for reels in video_reels
        ]

        response = schema.UserShemaForContent(
            id=current_user.id,
            username=current_user.username,
            profile_photo=current_user.profile_photo,
            content=content_response,
            history=history_response,
            name=current_user.name,
            surname=current_user.surname,
            biography=current_user.bigraph,
            email=current_user.email,
            content_count=content_count,
            who_followers_count=who_followed_user_count,
            followers_count = followers_count,
            history_count=history_count,
            reels=video_reels_response,
        )

        return response

    async def get_following_users(self, user_id: int, current_user: models.User):

        following_users = (
            self.session.query(models.User)
            .join(
                models.subscription, models.subscription.c.followed_id == models.User.id
            )
            .filter(models.subscription.c.follower_id == user_id)
            .all()
        )

        if not following_users:
            raise HTTPException(status_code=404, detail="You are not following anyone")

        following_response = [
            schema.UserShemaForContent(
                id=user.id,
                email=user.email,
                username=user.username,
                profile_photo=user.profile_photo,
            )
            for user in following_users
        ]

        return following_response

    async def get_subscribed_history(self, current_user: models.User):

        followed_ids = (
            self.session.query(models.subscription.c.followed_id)
            .filter(models.subscription.c.follower_id == current_user.id)
            .all()
        )

        followed_ids = [followed_id for (followed_id,) in followed_ids]

        if not followed_ids:
            raise HTTPException(status_code=404, detail="You are not following anyone")

        history = (
            self.session.query(models.History)
            .filter(models.History.author_id.in_(followed_ids))
            .all()
        )

        if not history:
            raise HTTPException(
                status_code=404, detail="No content found from followed users"
            )

        for item in history:
            author = (
                self.session.query(models.User)
                .filter(models.User.id == item.author_id)
                .first()
            )
            if not author:
                continue

            history_response = [
                schema.HistoryResponse(
                    id=item.id,
                    author=schema.UserShema(
                        id=item.author_id,
                        profile_photo=str(item.author.profile_photo),
                        username=str(item.author.username),
                    ),
                    content=item.content,
                    views_count=item.views_count,
                    created_at=item.created_at,
                    like_count=len(item.liked_by),
                )
            ]

        return history_response

    async def close_user_account(self, current_user: models.User):

        if current_user.is_closed == True:
            current_user.is_closed = False

            self.session.commit()

            return "Opened"

        else:
            current_user.is_closed = True

            self.session.commit()
            return "Is Closed"

    async def update_password(
        self,
        session: Session,
        current_user: models.User,
        old_password: str = Form(...),
        new_password: str = Form(...),
    ):
        if not Hash.verify(old_password, current_user.password):
            raise HTTPException(detail="Incorrect old password", status_code=402)

        if len(new_password) < 6:
            raise HTTPException(detail="Password too short", status_code=404)

        hashed_password = Hash.bcrypt(new_password)
        current_user.password = hashed_password

        session.add(current_user)
        session.commit()

        return {"message": "Your password was updated successfully."}