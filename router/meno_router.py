from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
import os 
import uuid
from datetime import datetime
from database import models, database, schema
from authentication.oauth import get_current_user  
from typing import List
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession


IMAGEDIR = 'media/images/'

router = APIRouter(
    tags=['Content'],
    prefix='/Content'
)

@router.post('/')
async def create_content(
    content_title: str = Form(...),
    file: UploadFile = File(...),
    # tagged_user: str = Form(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    content_for: schema.InteresingContentEnum = Form(...)
):
    

    # Сохраняем файл
    file.filename = f"{uuid.uuid4()}.jpg"
    contents = await file.read()
    file_path = os.path.join(IMAGEDIR, file.filename)
    with open(file_path, 'wb') as f:
        f.write(contents)

    new_content = models.Content(
        content_title=content_title,
        content_photo=file.filename,
        author_id=current_user.id,
        created_at=datetime.utcnow(),
        content_for = content_for
    )

    db.add(new_content)
    db.commit()
    db.refresh(new_content)

    return {"message": "Content created successfully", "content": new_content}


@router.get('/content/{id}', response_model=schema.ContentSchema)
async def get_content_with_primary_key(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    detail = db.query(models.Content).filter(models.Content.id == id).first()

    if not detail:
        raise HTTPException(detail=f'Content with id {id} not found', status_code=404)

    like = detail.liked_by
    like_count = len(like)

    existing_view = db.query(models.View).filter(
        models.View.content_id == id,
        models.View.user_id == current_user.id
    ).first()

    if not existing_view:
        new_view = models.View(
            content_id=id,
            user_id=current_user.id,
            timestamp=datetime.utcnow()
        )

        db.add(new_view)
        detail.view_count = (detail.view_count or 0) + 1
        db.commit()
        db.refresh(new_view)

    response_data = schema.ContentSchema(
        id=detail.id,
        content_title=detail.content_title,
        content_photo=detail.content_photo,
        author=detail.author.username,
        created_at=detail.created_at,
        profile_photo=detail.author.profile_photo,
        author_id=detail.author.id,
        view_count=detail.view_count,
        like_count=like_count
    )

    return response_data




@router.put("/{content_id}/like")
async def like_content(content_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    content = db.query(models.Content).filter(models.Content.id == content_id).first()


    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if current_user in content.liked_by:
        content.liked_by.remove(current_user)

    else:
        content.liked_by.append(current_user)

    db.commit()
    db.refresh(current_user)  
    db.refresh(content)      
    return {"message": "Content liked/unliked successfully"}


@router.put('/add-to-user-chosen/{id}/')
async def add_user_chosen(

    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),

):

    content = db.query(models.Content).filter(models.Content.id == id).first()

    if not content:
        raise HTTPException(detail=f'Content With id {id} Not found', status_code=404)
    
    if current_user in content.user_chosen:
        content.user_chosen.remove(current_user)
        return 'Added Succsesfully'

    else:
        content.user_chosen.append(current_user)

    db.commit()
    db.refresh(current_user)
    db.refresh(content)

    return {'detail': 'Added/Removed'}

@router.get('/popular/', response_model=List[schema.ContentSchema])
async def get_popular_content(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):

    subquery = (
        db.query(models.content_likes.c.content_id, func.count(models.content_likes.c.user_id).label('like_count'))
        .group_by(models.content_likes.c.content_id)
        .subquery()
    )


    popular_content_query = (
        db.query(models.Content, subquery.c.like_count)
        .join(subquery, models.Content.id == subquery.c.content_id)
        .order_by(models.Content.created_at.desc())
        .filter(subquery.c.like_count > 1)
        .all()
    )

    if not popular_content_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No popular content found")

    response = []
    for content, like_count in popular_content_query:
        response.append(schema.ContentSchema(
            id=content.id,
            content_photo=content.content_photo,
            content_title=content.content_title,
            author=str(content.author.username),
            profile_photo=content.author.profile_photo,
            view_count=content.view_count,
            created_at = content.created_at,
            like_count=like_count  
    ))

    return response



@router.delete('/{id}')
async def delete_content(id:int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):

    obj_for_delete = db.query(models.Content).filter(models.Content.id == id).first()

    if obj_for_delete:

        if obj_for_delete.author_id == current_user.id:

            db.delete(obj_for_delete)
            db.commit()

            return 'Delete Succsesfully'
    
    raise HTTPException(detail='Not Found', status_code=404)


@router.get('/user/views', response_model=List[schema.ContentSchema])
async def get_viewed_contents(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):

    viewed_content_ids = db.query(models.View.content_id).filter(
        models.View.user_id == current_user.id
    ).all()

    if not viewed_content_ids:
        return []

    viewed_contents = db.query(models.Content).order_by(models.Content.created_at.desc()).filter(
        models.Content.id.in_([vc[0] for vc in viewed_content_ids])
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
            view_count=content.view_count,
        )
        for content in viewed_contents
    ]

    return response_data


@router.get('/liked-contents', response_model=List[schema.ContentSchema])
async def get_user_liked_contents(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    liked_content_ids = db.query(models.content_likes.c.content_id).filter(
        models.content_likes.c.user_id == current_user.id
    ).all()

    if not liked_content_ids:
        return []

    liked_contents = db.query(models.Content).order_by(models.Content.created_at.desc()).filter(
        models.Content.id.in_([content_id[0] for content_id in liked_content_ids])
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




@router.get('/user-content', response_model=schema.ContentResponse)
async def get_user_content(

    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),

):
    
    content = db.query(models.Content).filter(models.Content.author_id == current_user.id).first()
    if content:
        
        response = schema.ContentResponse(
            id = content.id,
            content_title = content.content_title,
            content_photo = content.content_photo,
            author = str(content.author.username),
            author_id = content.author_id, 
            created_at = content.created_at,
            profile_photo = content.author.profile_photo
        )

        return response
    
    raise HTTPException(detail=[], status_code=404)


@router.get('/get-all-publication/', response_model=List[schema.ContentSchema])
async def get_all_publication(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    publication = db.query(models.Content).order_by(models.Content.created_at.desc()).all()

    response = [
        schema.ContentSchema(
            id=content.id,
            author_id=content.author_id,
            author = str(content.author.username),
            content_title=content.content_title,
            created_at=content.created_at,
            content_photo=content.content_photo,
            view_count=content.view_count,
            profile_photo = content.author.profile_photo
        ) for content in publication
    ]

    return response



@router.delete('{id}/')
async def delete(

    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),

):
    

    model = db.query(models.Content).filter(models.Content.id == id).first()

    if not model:
        raise HTTPException(detail='Object not found', status_code=404)

    db.delete(model)
    db.commit()
        
    return 'Deleted Succsesfully'


@router.get('/get-user-interesing-content/', response_model=List[schema.ContentSchema])
async def get_user_interesing_content(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Поиск контента, который интересует пользователя
    intresed_content = db.query(models.Content).filter(
        models.Content.content_for == current_user.creation_account_for
    ).order_by(models.Content.created_at.desc()).all()

    if not intresed_content:
        raise HTTPException(detail='Interesed content not found', status_code=404)

    response = [
        {
            "id": content.id,
            "author_id": content.author_id,
            "author": content.author.username,
            "content_title": content.content_title,
            "created_at": content.created_at,
            "content_photo": content.content_photo,
            "view_count": content.view_count,
            "profile_photo": content.author.profile_photo if content.author.profile_photo else None
        } for content in intresed_content
    ]

    return response



@router.put('update-content/{id}/')
async def update_content(

    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    content_title: str = Form(...),

):

    content = db.query(models.Content).filter(models.Content.id == id).first()

    if not content:
        raise HTTPException(detail= f'Content with id {id} not found', status_code=404)
    
    if current_user.id == content.author_id:
        
        content.content_title = content_title

        db.commit()

        return 'Content Updated Succsesfully'
    

