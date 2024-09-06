from fastapi import APIRouter, File, UploadFile, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from authentication.oauth import get_current_user
from database import models, database, schema
from services.api.v1.todo_service import ToDoService
from typing import List

IMAGEDIR = 'media/images/'

router = APIRouter(
    tags=['Todo'],
    prefix='/Todo'
)


@router.post('/create-to-do', response_model=schema.ToDoschema)
async def create_todo(

    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    title: str = Form(...),
    file: UploadFile = File(None),

):
    service = ToDoService(session=db)
    return await service.create_todo(current_user=current_user, title=title, file=file)

@router.get('/get-user-todo', response_model=List[schema.ToDoschema])
async def get_user_todo(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):

    service = ToDoService(session=db)
    return await service.get_user_todo(current_user=current_user)


@router.delete('delete-user-todo/{id}/')
async def delete(

    id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),

):
    
    service = ToDoService(session=db)
    return await service.delete(current_user=current_user, id=id)


@router.put('/{id}')
async def update(

    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    title: str = Form(...),
):
    
    
    service = ToDoService(session=db)
    return await service.update(current_user=current_user, title=title, id=id)