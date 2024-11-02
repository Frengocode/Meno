from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import socketio
from database import database, models
from authentication import authentication, user
from router import meno_router, todo, history, commentarion, chat, audio_transelter, video_reels, notification
from datetime import timedelta, datetime
from PIL import Image
from io import BytesIO
from database.database import Base, engine

Base.metadata.create_all(engine)

from sqladmin import Admin, ModelView

app = FastAPI(title='Meno')

app.include_router(authentication.router)
app.include_router(user.router)
app.include_router(meno_router.router)
app.include_router(chat.router)
app.include_router(history.router)
app.include_router(commentarion.router)
app.include_router(todo.router)
app.include_router(audio_transelter.audio_router)
app.include_router(video_reels.video_reels_router)
app.include_router(notification.notification_router)


origins = [
    "http://localhost",
    "http://localhost:8081",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



scheduler = BackgroundScheduler()
scheduler.start()

def delete_old_history():
    db: Session = database.SessionLocal()
    time_threshold = datetime.utcnow() - timedelta(hours=24)
    
    try:
        db.query(models.History).filter(models.History.created_at <= time_threshold).delete()
        db.commit()
    finally:
        db.close()

scheduler.add_job(delete_old_history, IntervalTrigger(minutes=10))

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()


