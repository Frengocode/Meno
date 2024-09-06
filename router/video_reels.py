from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session
from database.models import  User
from authentication.oauth import get_current_user
from database.database import get_db
from database import schema
from typing import List
import logging
from services.api.v1.video_reels_service import VideoReelService
import os

logger = logging.getLogger(__name__)


video_reels_router = APIRouter(tags=["Video Reels"])

MEDIA_ROOT = "media/reels/"


@video_reels_router.post("/create-video-reels/")
async def create_video_reels(
    reels_title: str = Form(...),
    video_reels: UploadFile = File(...),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    place: str = Form(None),
):

    service = VideoReelService(session=session)
    return await service.create_video_reels(reels_title=reels_title, video_reels=video_reels, current_user=current_user, place=place)
    

@video_reels_router.get("/get-reels/{id}/", response_model=schema.VideoReelsSchema)
async def get_reels(
    id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schema.VideoReelsSchema | None:

    service = VideoReelService(session=session)
    return await service.get_reels(id=id, current_user=current_user)



@video_reels_router.get("/get-all-reels", response_model=List[schema.VideoReelsSchema])
async def get_all_reels(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[schema.VideoReelsSchema]:

    service = VideoReelService(session=session)
    return await service.get_all_reels(current_user=current_user)




@video_reels_router.put("/like-button-for-reels/{reels_id}/")
async def like_button(
    reels_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    service = VideoReelService(session=session)
    return await service.like_button(reels_id=reels_id, current_user=current_user)



@video_reels_router.delete("/delete-reels/{reels_id}/")
async def delete_reels(
    reels_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):

    service = VideoReelService(session=session)
    return await service.delete_reels(reels_id=reels_id, current_user=current_user)


@video_reels_router.put('/update-video-reels/{reels_id}/')
async def update_video_reels(

    reels_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    reels_title: str = Form(...),
    place: str = Form(None)
):
    
    service = VideoReelService(session=session)
    return await service.update_video_reels(reels_id=reels_id, current_user=current_user, reels_title=reels_title, place=place)



@video_reels_router.put('/add-video-reels-to-archive/{video_reels}/')
async def add_archive(
    	
    reels_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user), 

):
    
    service  = VideoReelService(session=session)
    return await service.add_archive(reels_id=reels_id, current_user=current_user)



@video_reels_router.get('/get-user-liked-reels/', response_model=List[schema.VideoReelsSchema])
async def get_user_liked_contents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    service  = VideoReelService(session=db)
    return await service.get_user_liked_reels(current_user=current_user)


@video_reels_router.get('/top-reels/', response_model=List[schema.VideoReelsSchema])
async def get_top_reels(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[schema.VideoReelsSchema]:
    
    
    service = VideoReelService(session=session)
    return await service.get_top_reels(current_user=current_user)

import aiofiles
from fastapi.responses import StreamingResponse


@video_reels_router.get("/get_reels/{filename}")
async def get_video_reels_file(filename: str):
    file_path = os.path.join(MEDIA_ROOT, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    async def file_streamer(file_path):
        async with aiofiles.open(file_path, mode='rb') as file:
            chunk_size = 1024 * 1024 
            while chunk := await file.read(chunk_size):
                yield chunk
    
    return StreamingResponse(file_streamer(file_path), media_type="video/mp4")
