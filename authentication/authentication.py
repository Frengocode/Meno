from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .token import create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from database import  models, database
from .hash import Hash

router = APIRouter(
    tags=['Authentication'],
)


@router.post('/login')
def login(request:OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db) ):
    user = db.query(models.User).filter(models.User.username == request.username ).first()
    if not user:
        raise HTTPException(detail={'error': 'Invalid Creadion'}, status_code=402)

    if not Hash.bcrypt(request.password):
        raise HTTPException(detail=f'In Correct', status_code=402)

    access_token = create_access_token(
        data={"sub": user.username}
        )
    return {"access_token":access_token, "token_type":"bearer"}

