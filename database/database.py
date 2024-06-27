from sqlalchemy import create_engine, delete
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession


DATABASE_URL = 'postgresql://postgres:python$_venv@localhost:5432/Meno'

engine = create_engine(DATABASE_URL, echo=True)

Base = declarative_base()
 
SessionLocal = sessionmaker(bind=engine, autoflush=False)



async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()