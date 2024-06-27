from fastapi import APIRouter, File, UploadFile, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from authentication.oauth import get_current_user
from database import models, database, schema
import os
import uuid
from datetime import datetime


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
    if file is not None:

        file.filename = f"{uuid.uuid4()}.jpg"
        contents = await file.read()


        file_path = os.path.join(IMAGEDIR, file.filename)
        with open(file_path, 'wb') as f:
            f.write(contents)

    
    new_todo_obj = models.UserToDo(
        
        title = title,
        user_id = current_user.id,
        # user = current_user.username,
        file = file.filename if file else None,
        created_at = datetime.utcnow()

    )


    db.add(new_todo_obj)
    db.commit()

    return new_todo_obj

from typing import List

@router.get('/get-user-todo', response_model=List[schema.ToDoschema])
async def get_user_todo(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):

    todo_objs = db.query(models.UserToDo).filter(
        models.UserToDo.user_id == current_user.id
    ).order_by(models.UserToDo.created_at.desc()).all()

    if not todo_objs:
        raise HTTPException(status_code=404, detail='You don\'t have any todos')

    response = [schema.ToDoschema(
        id=todo.id,
        user_id=todo.user_id,
        title=todo.title,
        created_at=todo.created_at,
        file=todo.file
    ) for todo in todo_objs]

    return response


@router.delete('delete-user-todo/{id}/')
async def delete(

    id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),

):
    
    todo = db.query(models.UserToDo).filter(models.UserToDo.id == id).first()

    if todo:
        if  current_user.id == todo.user_id:

            db.delete(todo)
            db.commit()
            
            return 'Todo Deleted Succsesfully'
        
    else:
        raise HTTPException(detail=f'ToDo with id {id} not fount', status_code=404)
    


@router.put('/{id}')
async def update(

    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    title: str = Form(...),
):
    
    
    todo_model = db.query(models.UserToDo).filter(models.UserToDo.id == id).first()

    if not todo_model:
        raise HTTPException(detail='Not Dound', status_code=404)
    
    if current_user.id == todo_model.user_id:

        todo_model.title = title

        db.commit()

        return 'Updated Succsesfully'
    
    raise HTTPException(detail='Author error', status_code=402)
    