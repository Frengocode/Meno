from fastapi import APIRouter, Depends, Form, HTTPException
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from database import models, database, schema
from authentication.oauth import get_current_user




router = APIRouter(
    prefix='/Commentarion',
    tags=['Comment']
)




@router.post('/{content_id}/')
async def create_commentarion(

    content_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session  = Depends(database.get_db),
    title: str = Form(...)

):
    
    content = db.query(models.Content).filter(models.Content.id == content_id).first()

    if content:

        new_commentarion_obj = models.CommentarionModel(
            title = title,
            user_id = int(current_user.id),
            date_pub = datetime.utcnow(),
            content = content
        ) 

        db.add(new_commentarion_obj)
        db.commit()
        db.refresh(new_commentarion_obj)

        return new_commentarion_obj
    

@router.get('/{content_id}/comments', response_model=List[schema.CommentResponse])
async def get_comments(
    content_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):

    content_model = db.query(models.Content).filter(models.Content.id == content_id).first()

    if not content_model:
        raise HTTPException(status_code=404, detail="Content not found")

    comments = db.query(models.CommentarionModel).filter(models.CommentarionModel.content_id == content_id).order_by(models.CommentarionModel.date_pub.desc()).all()

    if not comments:
        raise HTTPException(status_code=404, detail="No comments found for this content")

    response = []
    for comment in comments:
        response.append(schema.CommentResponse(
            id=comment.id,
            content_id=comment.content_id,
            user = str(comment.user.username),
            title=  str(comment.title),
            user_id=comment.user_id,
            date_pub=comment.date_pub,
            profile_photo = str(comment.user.profile_photo)
        ))

    return response


@router.delete('/{id}')
async def delete(
    
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)):

    comment = db.query(models.CommentarionModel).filter(models.CommentarionModel.id == id).first()

    if comment:

        if comment.user_id == comment.user_id:

            db.delete(comment)
            db.commit()
            return 'Comment Deleted Succsesfully'

    raise HTTPException(detail=f'Commentarion with {id} not found', status_code=404) 
   
