from fastapi import APIRouter, Depends, Form
from typing import List
from sqlalchemy.orm import Session
from database import models, database, schema
from authentication.oauth import get_current_user
from services.api.v1.commentarion_service import CommentarionService

router = APIRouter(tags=["Comment"])


@router.post("/create-comment/{content_id}/")
async def create_commentarion(
    content_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),
    title: str = Form(...),
):

    services = CommentarionService(session=db)
    return await services.create_commentarion(
        content_id=content_id, current_user=current_user, title=title
    )


@router.get("/get-comments/{content_id}/", response_model=List[schema.CommentResponse])
async def get_comments(
    content_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):

    services = CommentarionService(session=db)
    return await services.get_comments(content_id=content_id, current_user=current_user)


@router.delete("/delete-comment/{id}")
async def delete(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):

    services = CommentarionService(session=db)
    return await services.delete(id=id, current_user=current_user)


@router.post("/create-comment-for-reels/{reels_id}/")
async def create_comment_for_reels(
    reels_id: int,
    session: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    comment: str = Form(...),
):

    services = CommentarionService(session=session)
    return await services.create_comment_for_reels(
        reels_id=reels_id, current_user=current_user, comment=comment
    )


@router.get(
    "/get-comments-from-reels/{reels_id}/", response_model=List[schema.CommentResponse]
)
async def get_comments_from_reels(
    reels_id: int,
    session: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
) -> List[schema.CommentResponse] | None:

    services = CommentarionService(session=session)
    return await services.get_comments_from_reels(
        reels_id=reels_id, current_user=current_user
    )
