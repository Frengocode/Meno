from fastapi import FastAPI
from router import meno_router, todo, history, commentarion, chat
from database import database
from authentication import authentication, user
from fastapi.middleware.cors import CORSMiddleware


database.Base.metadata.create_all(database.engine)



app = FastAPI(
    title='Meno'
)

app.include_router(authentication.router)
app.include_router(user.router)
app.include_router(meno_router.router)
app.include_router(chat.router)
app.include_router(history.router)
app.include_router(commentarion.router)
app.include_router(todo.router)




origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


