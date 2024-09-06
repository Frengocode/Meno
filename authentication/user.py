from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from database import schema, database, models
from .oauth import get_current_user
from sqlalchemy.orm import Session
import os
from services.api.v1.user_service import UserService
from typing import List


router = APIRouter(tags=["User"])


IMAGEDIR = "media/images/"


@router.post("/sign_up/")
async def create_new_user(
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
):

    service = UserService(session=db)

    return await service.create_new_user(
        username=username, password=password, email=email, file=file
    )


@router.get("/user/{user_id}", response_model=schema.UserShemaForContent)
async def get_user(
    category: schema.InteresingContentEnum,
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),

):
    serivice = UserService(session=db)

    return await serivice.get_user_with_id(user_id, current_user=current_user, content_category=category)


@router.get("/file/{filename}")
async def get_profile_photo(filename: str):
    file_path = os.path.join(IMAGEDIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@router.patch("/update-user-components/", response_model=schema.UserUpdateResponse)
async def update_username(
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user),
    username: str = Form(...),
    surname: str = Form(None),
    name: str = Form(None),
    biography: str = Form(None),
    file: UploadFile = File(None)
) -> schema.UserUpdateResponse:
    


    service = UserService(session=db)
    return await service.update_username(
        current_user=current_user,
        username=username,
        surname=surname,
        name=name,
        biography=biography,
        file=file
    )


@router.post("/follow/{user_id}")
async def follow_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):

    service = UserService(session=db)
    return await service.follow_user(user_id=user_id, current_user=current_user)


@router.post("/unfollow/{id}")
async def unfollow(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):

    service = UserService(session=db)
    return await service.unfollow(id=id, current_user=current_user)




@router.get("/subscriptions/content", response_model=List[schema.ContentSchema])
async def get_subscribed_content(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):

    service = UserService(session=db)

    return await service.get_subscribed_content(current_user=current_user)



@router.get(
    "/get-who-subscriped/{user_id}/", response_model=List[schema.UserShemaForContent]
)
async def get_following_users(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):

    service = UserService(session=db)
    return await service.get_following_users(user_id=user_id, current_user=current_user)


@router.get(
    "/get-followers/{user_id}/", response_model=List[schema.UserShemaForContent]
)
async def get_followers_users(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):

    service = UserService(session=db)

    return await service.get_followers_users(user_id=user_id, current_user=current_user)


@router.get("/get-user-chosen", response_model=List[schema.ContentSchema])
async def get_user_liked_contents(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    service = UserService(session=db)

    return await service.get_user_chosen_contents(current_user=current_user)


@router.get("/search-users/", response_model=List[schema.UserShema])
async def search_users(
    username: str = None,
    session: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
) -> List[schema.UserShema]:

    service = UserService(session=session)
    return await service.search_users(username=username, current_user=current_user)


@router.get("/user-me/", response_model=schema.UserShemaForContent)
async def user_me(
    session: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):

    serivece = UserService(session=session)
    return await serivece.user_me(current_user=current_user)


@router.get("/subscriptions/history", response_model=List[schema.HistoryResponse])
async def get_subscribed_history(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):

    serivece = UserService(session=db)
    return await serivece.get_subscribed_history(current_user=current_user)


@router.patch("/close-user-account/")
async def close_user_account(
    session: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    serivece = UserService(session=session)
    return await serivece.close_user_account(current_user=current_user)


@router.patch("/update-password/")
async def update_password(
    session: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    old_password: str = Form(...),
    new_password: str = Form(...),
):

    serivece = UserService(session=session)
    return await serivece.update_password(current_user=current_user, old_password=old_password, new_password=new_password, session=session)

