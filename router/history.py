from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from database import models, schema, database
from authentication.oauth import get_current_user
from services.api.v1.history_service import HistoryService

IMAGEDIR = "media/images/"

router = APIRouter(prefix="/History", tags=["History"])


@router.post("/")
async def create_history(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    file: UploadFile = File(...),
):

    service = HistoryService(session=db)
    return await service.create_history(file=file, current_user=current_user)


@router.put("/{id}")
async def like_button(
    history_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):

    service = HistoryService(session=db)
    return await service.like_button(history_id=history_id, current_user=current_user)


@router.get("/history/{id}", response_model=schema.HistoryResponse)
async def get_content_with_primary_key(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):

    service = HistoryService(session=db)
    return await service.get_history_with_primary_key(id=id, current_user=current_user)


@router.delete("delete-history/{id}")
async def delete_history(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):

    service = HistoryService(session=db)
    return await service.delete_history(id=id, current_user=current_user)
