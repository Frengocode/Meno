from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.orm import Session
from database import models, schema, database
from authentication.oauth import get_current_user
import os
import uuid
from datetime import timedelta, datetime

IMAGEDIR = 'media/images/'

router = APIRouter(
    prefix='/History',
    tags=['History']
)


@router.post('/')
async def create_history(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    file: UploadFile = File(...),  
):


    file.filename = f"{uuid.uuid4()}.jpg"
    history = await file.read()

    file_path = os.path.join(IMAGEDIR, file.filename)
    with open(file_path, 'wb') as f:
        f.write(history)

    new_history_obj = models.History(
        content=file.filename,
        author_id=current_user.id,
        created_at=datetime.utcnow(),
        delete_at=datetime.utcnow() + timedelta(days=1)
    )



    db.add(new_history_obj)
    db.commit()

    return {"message": "Content created successfully", "content": new_history_obj}




@router.put('/{id}')
async def like_button(

    history_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),

    ):

    history_model = db.query(models.History).filter(models.History.id == history_id).first()


    if not history_model:
        raise HTTPException(detail='History Not found', status_code=404)
    

    if current_user in history_model.liked_by:
        history_model.liked_by.remove(current_user)

    else:
        history_model.liked_by.append(current_user)

    db.commit()
    db.refresh(current_user)  
    db.refresh(history_model)
    return {"message": "Content liked/unliked successfully"}






@router.get('/history/{id}', response_model=schema.HistoryResponse)
async def get_content_with_primary_key(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    
    detail = db.query(models.History).filter(models.History.id == id).first()

    if not detail:
        raise HTTPException(status_code=404, detail=f'Content with id {id} not found')

    existing_view = db.query(models.View).filter(
        models.View.history_id == id,
        models.View.user_id == current_user.id
    ).first()

    if not existing_view:

        new_view = models.View(
            history_id=id,
            user_id=current_user.id,
            timestamp=datetime.utcnow()
        )

        db.add(new_view)
        
        detail.views_count = (detail.views_count or 0) + 1
        db.commit()
        db.refresh(new_view)


    like = detail.liked_by
    likes_count = len(like)


    response_data = schema.HistoryResponse(
        id=detail.id,
        author=detail.author.username,
        created_at=detail.created_at,
        profile_photo=detail.author.profile_photo,
        author_id=detail.author.id,
        views_count=detail.views_count,
        like_count=likes_count
    )

    return response_data


@router.delete('delete-history/{id}')
async def delete_history(

    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),

):
    
    history_obj = db.query(models.History).filter(models.History.id == id).first()

    if not history_obj:
        raise HTTPException(detail='Not found', status_code=404)
    
    if current_user.id == history_obj.author_id:

        db.delete(history_obj)
        db.commit()
        
        return {'message': 'History Deleted Succsesfully'}