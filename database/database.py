from sqlalchemy import create_engine, delete
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DATABASE_URL = 'postgresql://username:password@localhost:5432/Meno'

engine = create_engine(DATABASE_URL, echo=True)

Base = declarative_base()
 
SessionLocal = sessionmaker(bind=engine, autoflush=False)


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
