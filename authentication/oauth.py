from fastapi import Depends, HTTPException, status
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from .token import SECRET_KEY, ALGORITHM
from database import models
from database.database import get_db
from database import schema
from sqlalchemy.orm import Session


oauth2_schema = OAuth2PasswordBearer(tokenUrl='login')

async def get_current_user(token: Annotated[str, Depends(oauth2_schema)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Can you please log in again to verify your identity",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user