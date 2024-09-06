from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import models, database, schema
from authentication.oauth import get_current_user
from typing import List
from services.api.v1.meno_service import MenoService


IMAGEDIR = "media/images/"

router = APIRouter(
    tags=["Content"],
)


@router.post("/create-content/")
async def create_content(
    content_title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    content_for: schema.InteresingContentEnum = Form(...),
):
    service = MenoService(session=db)

    return await service.create_content(
        content_for=content_for,
        current_user=current_user,
        content_title=content_title,
        file=file,
    )


@router.get("/content/{id}", response_model=schema.ContentSchema)
async def get_content_with_primary_key(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):

    service = MenoService(session=db)

    return await service.get_content_with_primary_key(id=id, current_user=current_user)


@router.put("/{content_id}/like")
async def like_content(
    content_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):

    service = MenoService(session=db)

    return await service.like_content(content_id=content_id, current_user=current_user)


@router.put("/add-to-user-chosen/{id}/")
async def add_user_chosen(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):

    service = MenoService(session=db)
    return await service.add_user_chosen(id=id, current_user=current_user)


@router.get("/popular/", response_model=List[schema.ContentSchema])
async def get_popular_content(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):

    service = MenoService(session=db)

    return await service.get_popular_content(current_user=current_user)


@router.get("/content/viewed-contents/", response_model=List[schema.ContentSchema])
async def get_viewed_contents(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):

    service = MenoService(session=db)

    return await service.get_viewed_contents(current_user=current_user)


@router.get("/liked-contents", response_model=List[schema.ContentSchema])
async def get_user_liked_contents(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):

    service = MenoService(session=db)
    return await service.get_user_liked_contents(current_user=current_user)


@router.get("/get-all-publication/", response_model=List[schema.ContentSchema])
async def get_all_publication(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    service = MenoService(session=db)

    return await service.get_all_publication(current_user=current_user)


@router.delete("/delete-content/{content_id}/")
async def delete(
    content_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):

    service = MenoService(session=db)

    return await service.delete(content_id=content_id, current_user=current_user)


@router.put("/content/update-content/{id}/")
async def update_content(

    id: int,
    content_for: schema.InteresingContentEnum,
    content_title: str = Form(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),

):
    
    content_categry = content_for.value

    service = MenoService(session=db)
    return await service.update_content(
        content_title=content_title, current_user=current_user, id=id, content_for=content_categry
    )


@router.get("/get-intering-contents/", response_model=List[schema.ContentSchema])
async def get_intering_contents(
    category: schema.InteresingContentEnum,
    session: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):

    service = MenoService(session=session)

    return await service.get_intering_contents(
        category=category, current_user=current_user
    )


@router.put("/add-to-archive/{content_id}/")
async def add_content_to_archive(
    content_id: int,
    session: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    service = MenoService(session=session)

    return await service.add_content_to_archive(
        content_id=content_id, current_user=current_user
    )


@router.get("/get-all-archived-contents/", response_model=List[schema.ContentSchema])
async def get_all_archived_contents(
    session: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
) -> List[schema.ContentSchema] | None:

    service = MenoService(session=session)

    return await service.get_all_archived_contents(current_user=current_user)


@router.get(
    "/get-likes-from-content/{content_id}/",
    response_model=List[schema.UserShemaForContent],
)
async def get_likes_from_content(
    content_id: int,
    session: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):

    service = MenoService(session=session)

    return await service.get_likes_from_content(
        content_id=content_id, current_user=current_user
    )
