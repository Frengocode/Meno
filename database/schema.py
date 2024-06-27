from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MessageUpdate(BaseModel):
    
    id: int
    message: str
    author_id: int
    is_updated: bool =  False 
    timestap: datetime


class InteresingContentEnum(Enum):

    for_any = 'for-any'
    for_grandmother = 'for_grandmother'
    for_grandfather = 'for_grandfather'
    for_kids = 'for-kids'

class TokenData(BaseModel):
    username: Optional[str] = None


class CreateUserShema(BaseModel):
    username: str
    password: str
    email: EmailStr


class Content(BaseModel):
    id: int
    author_id: int
    timestamp: datetime
    sender_username: str
    content_photo: str
    sender_profile_photo: str

class ContentResponse(BaseModel):
    id: int
    content_title: str
    content_photo: Optional[str]   
    author_id: int
    author: str
    created_at: datetime
    profile_photo: str

    class Config:
        orm_mode = True



class UserShema(BaseModel):

    id: int
    email:str
    username: str
    profile_photo: Optional[str] = None
    
      

class ContentSchema(BaseModel):
    id: int
    content_title: str
    content_photo: Optional[str]
    author: Optional[str] = None
    created_at: datetime
    like_count: int = 0  
    liked_by: List[str] = []

    profile_photo: Optional[str] = None
    author_id: Optional[int] = None
    view_count: int
    tagged_user: Optional[str] = None
    content_for: Optional[InteresingContentEnum] = None

    class Config:
        orm_mode = True

class HistoryResponse(BaseModel):

    id: int
    author_id: int
    profile_photo: Optional[str] = None
    created_at: datetime
    like_count: int
    views_count: Optional[int] = 0
    author: str
    

    class Config:
        orm_mode = True

class UserShemaForContent(BaseModel):


    id: int
    email:str
    username: str

    
    name: Optional[str] = None
    surname: Optional[str] = None
    biography: Optional[str] = None
    # birthday_date: datetime = None

    content_count: int = 0
    followers_count: Optional[int] = None
    history: Optional[List[HistoryResponse]] = None
    profile_photo: Optional[str] = None
    content: Optional[List[ContentResponse]] = None
    history: Optional[List[HistoryResponse]] = None

    interesing_content : Optional[InteresingContentEnum] = None





class UserContentResponse(BaseModel):
    id: int
    sender_id: int
    content_id: int
    chat_id: int
    created_at: datetime


class UserUpdateResponse(BaseModel):
    id: int
    username: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    intered_content: Optional[InteresingContentEnum] = None
    biography: Optional[str] = None 





class ChatCreate(BaseModel):
    participants: List[int]

class ChatResponse(BaseModel):
    id: int
    participants: List[int]
    messages: List[Optional['MessageResponse']]
    content: List[int]

    class Config:
        orm_mode = True


class SendContentRequest(BaseModel):
    recipient_id: int
    content_id: int
    chat_id: int


class MessageResponse(BaseModel):
    id: int
    content: str
    img_file: Optional[str]
    author_id: int
    chat_id: int

    class Config:
        orm_mode = True



class CommentResponse(BaseModel):
    id: int
    date_pub: datetime
    user_id: int
    content_id: int
    user: str
    title: str
    profile_photo: str


class ToDoschema(BaseModel):

    id: int
    created_at: datetime
    user_id: int
    title: str
    file: Optional[str] = None



class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    img_file: Optional[str] = None

class Message(MessageBase):
    id: int
    author_id: int
    img_file: Optional[str] = None
    chat_id: int
    timestamp: datetime
    profile_photo: str
    author: str

    class Config:
        orm_mode = True

class ChatBase(BaseModel):
    participants: List[int]

class ChatCreate(ChatBase):
    pass

class ChatParticipant(BaseModel):
    id: int
    username: str
    user_id: int
    profile_photo: Optional[str] = None

class Chat(ChatBase):
    id: int
    messages: List[Message] = []
    participants: List[ChatParticipant]
    contents: List[Content] = None
    

    class Config:
        orm_mode = True