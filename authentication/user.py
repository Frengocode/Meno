from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import  FileResponse
from database import schema, database, models
from .oauth import get_current_user
from .hash import Hash
from sqlalchemy.orm import Session
import uuid
import os
from datetime import datetime


router  = APIRouter(
    prefix='/User',
    tags=['User']
)


IMAGEDIR = 'media/images/'


@router.post('/')
async def create_new_user(
    creation_account_for: schema.InteresingContentEnum = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),

):
    
    file.filename = f"{uuid.uuid4()}.jpg"
    contents = await file.read()

    file_path = os.path.join(IMAGEDIR, file.filename)
    with open(file_path, 'wb') as f:
        f.write(contents)

    exist_username = db.query(models.User).filter(models.User.username == username).first()
    if exist_username:
        raise HTTPException(detail=f'{username} already exists', status_code=400)

    exist_email = db.query(models.User).filter(models.User.email == email).first()
    if exist_email:
        raise HTTPException(detail=f'{email} already exists', status_code=400)

    if not email.endswith('@gmail.com'):
        raise HTTPException(detail='Email must end with @gmail.com', status_code=400)

    hashed_password = Hash.bcrypt(password)

    new_user = models.User(
        username=username,
        email=email,
        password=hashed_password,
        profile_photo=file.filename,
        creation_account_for = creation_account_for
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user



@router.get('/user/{user_id}', response_model=schema.UserShemaForContent)
async def get_user_with_profile_photo(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_contents = []
    contents = db.query(models.Content).filter(models.Content.author_id == user_id).order_by(models.Content.created_at.desc()).all()

    followers =  user.followed_by
    followers_count = len(followers)

    content = user.content
    content_count = len(content)

    

    for content in contents:
        content_schema = schema.ContentResponse(
            id=content.id,
            content_title=content.content_title,
            content_photo=content.content_photo,
            author_id=content.author_id,
            created_at=content.created_at,
            author=user.username,
            profile_photo=user.profile_photo,
        )
        user_contents.append(content_schema)

    user_histories = []
    histories = db.query(models.History).filter(models.History.author_id == user_id).order_by(models.History.created_at.desc()).all()



    for history in histories:

        likes = history.liked_by
        like_count = len(likes)

        history_response = schema.HistoryResponse(
            id=history.id,
            author_id=history.author_id,
            created_at=history.created_at,
            profile_photo=user.profile_photo,
            views_count = history.views_count,
            author = str(history.author.username),
            like_count = like_count
        )
        user_histories.append(history_response)

    user_schema = schema.UserShemaForContent(
        id=user.id,
        email=user.email,
        username=user.username,
        followers_count = followers_count,
        profile_photo=user.profile_photo,
        content=user_contents,
        history=user_histories,
        content_count = content_count,

        name = str(user.name),
        surname = str(user.surname),
        biography = str(user.bigraph),
        birthday_date = user.birthday_date,
    )

    return user_schema



@router.get('/file/{filename}')
async def get_profile_photo(filename: str):
    file_path = os.path.join(IMAGEDIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)



@router.patch('/update', response_model=schema.UserUpdateResponse)
async def update_username(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    username: str = Form(...),
    surname: str = Form(None),
    name: str = Form(None),
    biography: str = Form(None),
    interesed_content: schema.InteresingContentEnum = Form(...)
):

    exist_username = db.query(models.User).filter(models.User.username == username).first()
    if exist_username:
        raise HTTPException(detail='Username already exists', status_code=status.HTTP_409_CONFLICT)

    current_user.username = username
    current_user.name = name
    current_user.surname  = surname
    current_user.creation_account_for = interesed_content.value
    current_user.bigraph = biography



    if  len(username) < 4:
        raise HTTPException(detail='Username Most Small', status_code=402)

    db.commit()
    db.refresh(current_user)


    return  schema.UserUpdateResponse(
        id=current_user.id,
        username=current_user.username,
        name = current_user.name,
        surname = current_user.surname,
        intered_content = interesed_content,
        biography = current_user.bigraph

    )



@router.post("/follow/{user_id}")
def follow_user(user_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself.")

    user_to_follow = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_follow:
        raise HTTPException(status_code=404, detail="User not found.")

    if user_to_follow in current_user.followed_by:

        raise HTTPException(status_code=400, detail="You are already following this user.")

    current_user.followed_by.append(user_to_follow)
    db.commit()

    return {"message": "You have successfully followed the user."}


@router.post('/unfollow/{id}')
async def unfollow(id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.id == id:
        raise HTTPException(status_code=400, detail="You cannot unfollow yourself.")

    user_to_unfollow = db.query(models.User).filter(models.User.id == id).first()
    if not user_to_unfollow:
        raise HTTPException(status_code=404, detail="User not found.")

    existing_subscription = db.execute(
        models.subscription.select().where(
            models.subscription.c.follower_id == current_user.id,
            models.subscription.c.followed_id == id
        )
    ).fetchone()

    if existing_subscription:
        db.execute(
            models.subscription.delete().where(
                models.subscription.c.follower_id == current_user.id,
                models.subscription.c.followed_id == id
            )
        )
        db.commit()
        return {"message": "Successfully unfollowed the user."}
    else:
        raise HTTPException(status_code=404, detail="You are not following this user.")



from typing import List

@router.get('/subscriptions/content', response_model=List[schema.ContentSchema])
async def get_subscribed_content(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    following_ids = [user.id for user in current_user.following]  # Получение ID пользователей, на которых подписан текущий пользователь

    if not following_ids:
        raise HTTPException(status_code=404, detail="You are not following anyone")

    content = db.query(models.Content).filter(models.Content.author_id.in_(following_ids)).all()

    if not content:
        raise HTTPException(status_code=404, detail="No content found from followed users")

    content_response = []
    for item in content:
        author = db.query(models.User).filter(models.User.id == item.author_id).first()
        if not author:
            continue  

        content_response.append(schema.ContentSchema(
            id=item.id,
            content_title=item.content_title,
            content_photo=item.content_photo,
            author=author.username,   
            created_at=item.created_at.strftime('%Y-%m-%d %H:%M:%S'), 
            like_count=0,   
            liked_by=[],  
            profile_photo=author.profile_photo,
            author_id = item.author_id,
            view_count = item.view_count
        ))

    return content_response


@router.get("/subscriptions", response_model=List[schema.UserShema])
def get_following_users(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    
    following_users = current_user.following

    if not following_users:
        raise HTTPException(status_code=404, detail="You are not following anyone")

    following_response = [
        schema.UserShema(
            id=user.id,
            email=user.email,
            username=user.username,
            profile_photo=user.profile_photo
        ) for user in following_users

    ]

    return following_response



@router.get('/get-user-chosen', response_model=List[schema.ContentSchema])
async def get_user_liked_contents(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    chosen_content_ids = db.query(models.chosen.c.content_id).filter(
        models.chosen.c.user_id == current_user.id
    ).all()

    if not chosen_content_ids:
        return []

    liked_contents = db.query(models.Content).filter(
        models.Content.id.in_([content_id[0] for content_id in chosen_content_ids])
    ).all()

    response_data = [
        schema.ContentSchema(
            id=content.id,
            content_title=content.content_title,
            content_photo=content.content_photo,
            author=content.author.username,
            created_at=content.created_at,
            profile_photo=content.author.profile_photo,
            author_id=content.author.id,
            view_count=content.view_count
        )
        for content in liked_contents
    ]

    return response_data

 