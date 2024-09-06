from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from database import models, database
from services.api.v1.authentication_services import AuthenticationService


router = APIRouter(
    tags=["Authentication"],
)


@router.post("/login")
async def login(
    request: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(database.get_db),
):
    
    services = AuthenticationService(session=session)
    return await services.login(request=request)
