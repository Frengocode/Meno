from fastapi import APIRouter, File, UploadFile, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from authentication.oauth import get_current_user
from database import models, database, schema
import os
import uuid
from datetime import datetime


IMAGEDIR = "media/images/"


class ToDoService:
    def __init__(self, session: Session):
        self.session = session

    async def create_todo(
        self,
        current_user: models.User,
        title: str = Form(...),
        file: UploadFile = File(None),
    ):
        if file is not None:

            file.filename = f"{uuid.uuid4()}.jpg"
            contents = await file.read()

            file_path = os.path.join(IMAGEDIR, file.filename)
            with open(file_path, "wb") as f:
                f.write(contents)

        new_todo_obj = models.UserToDo(
            title=title,
            user_id=current_user.id,
            # user = current_user.username,
            file=file.filename if file else None,
            created_at=datetime.utcnow(),
        )

        self.session.add(new_todo_obj)
        self.session.commit()

        return new_todo_obj

    async def get_user_todo(
        self,
        current_user: models.User,
    ):

        todo_objs = (
            self.session.query(models.UserToDo)
            .filter(models.UserToDo.user_id == current_user.id)
            .order_by(models.UserToDo.created_at.desc())
            .all()
        )

        if not todo_objs:
            raise HTTPException(status_code=404, detail="You don't have any todos")

        response = [
            schema.ToDoschema(
                id=todo.id,
                user_id=todo.user_id,
                title=todo.title,
                created_at=todo.created_at,
                file=todo.file,
            )
            for todo in todo_objs
        ]

        return response

    async def delete(
        self,
        id: int,
        current_user: models.User,
    ):

        todo = (
            self.session.query(models.UserToDo).filter(models.UserToDo.id == id).first()
        )

        if todo:
            if current_user.id == todo.user_id:

                self.session.delete(todo)
                self.session.commit()

                return "Todo Deleted Succsesfully"

        else:
            raise HTTPException(detail=f"ToDo with id {id} not fount", status_code=404)

    async def update(
        self,
        id: int,
        current_user: models.User,
        title: str = Form(...),
    ):

        todo_model = (
            self.session.query(models.UserToDo).filter(models.UserToDo.id == id).first()
        )

        if not todo_model:
            raise HTTPException(detail="Not Dound", status_code=404)

        if current_user.id == todo_model.user_id:

            todo_model.title = title

            self.session.commit()

            return "Updated Succsesfully"

        raise HTTPException(detail="Author error", status_code=402)
