from fastapi import  HTTPException
from sqlalchemy.orm import Session
from authentication.token import create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from database import models
from authentication.hash import Hash
from sqlalchemy import select


class AuthenticationService:
    def __init__(self, session: Session):
        self.session = session

    async def login(self, request: OAuth2PasswordRequestForm):
        user_result = self.session.execute(
            select(models.User).filter(models.User.username == request.username)
        )

        user = user_result.scalars().first()

        if not user:
            raise HTTPException(detail={"error": "Invalid Creadion"}, status_code=402)

        if not Hash.verify(request.password, user.password):
            raise HTTPException(detail=f"In Correct", status_code=402)

        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}