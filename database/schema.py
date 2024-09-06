from pydantic import BaseModel, EmailStr
from typing import Optional, List, Union
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
    content_creator_username: str
    content_creator_profile_photo: Optional[str] = None

    author_id: int
    timestamp: datetime
    sender_username: str
    content_photo: str
    sender_profile_photo: str

    sender_id: int

    # column for Chat 

    message_sending_content: Optional[str] = None
    user_content_id: Optional[int] = None

class ContentResponse(BaseModel):
    id: int
    content_title: str
    content_photo: Optional[str]   
    author_id: int
    author: str
    created_at: datetime
    profile_photo: str
    like_count: int = 0
    view_count: int = 0

    class Config:
        orm_mode = True



class UserShema(BaseModel):

    id: int
    email: Optional[str] = None
    username: Optional[str] = None
    profile_photo: Optional[str] = None
    
    # chat atrebutes

    sender_username: Optional[str] = None
    sender_profile_photo: Optional[str] = None
    user_content_id: Optional[int] = None

class VideoReelsSchema(BaseModel):
    id: int
    video_reels: str
    reels_title: str
    user: Optional[UserShema] = None
    created_at: datetime
    is_archived: Optional[bool] = None
    like_count: Optional[int] = None
    view_count: int
    place: Optional[str] = None
    views_for_detail_page: Optional[List[UserShema]] = None
    who_liked: Optional[Union[list[UserShema], UserShema]] = None
    who_viewed: Optional[UserShema] = None

    sender_id: Optional[int] = None
    sender_username: Optional[str] = None
    sender_profile_photo: Optional[str] = None
    commentarion_count: Optional[int] = 0
    
    shered_count: Optional[int] = None


    # Chat column 

    message_sended_content: Optional[str] = None
    user_content_id: Optional[int] = None
    

class ContentSchema(BaseModel):
    id: int
    content_title: str
    content_photo: Optional[str] = None
    created_at: datetime
    view_count: Optional[int] = None
    author: Optional[UserShema] = None
    profile_photo: Optional[str] = None
    like_count: Optional[int] = None
    shered_counts: Optional[int] = None
    commentarion_count: Optional[int] = None

class HistoryResponse(BaseModel):
    id: int
    created_at: datetime
    views_count: int
    author: Optional[UserShema] = None
    like_count: Optional[int] = 0
    content: str
    who_viewed: Optional[UserShema] = None
    who_liked: Optional[UserShema] = None

class UserShemaForContent(BaseModel):
    id: int
    email: Optional[str] = None
    username: str
    is_following: bool = False
    name: Optional[str] = None
    surname: Optional[str] = None
    biography: Optional[str] = None
    content_count: Optional[int] = None
    who_followers_count: Optional[int] = None
    followers_count: int = 0
    history: Optional[List[HistoryResponse]] = None
    profile_photo: Optional[str] = None
    content: Optional[List[ContentSchema]] = None
    commentarion_count: int = 0
    shred_counts: int = 0
    history_count: int = 0
    interesing_content: Optional[str] = None  
    is_closed: Optional[bool] = None
    reels: Optional[List[VideoReelsSchema]] = None

    get_content_with_category: Optional[List[ContentSchema]] = None




class UserContentResponse(BaseModel):
    id: int
    sender_id: int
    content_id: Optional[int] = None
    chat_id: int
    created_at: datetime
    message_for_sending_content: Optional[str] = None


class UserUpdateResponse(BaseModel):
    id: int
    username: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    intered_content: Optional[InteresingContentEnum] = None
    biography: Optional[str] = None 
    profile_photo: Optional[str] = None




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
    content_id: Optional[int] = None 
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
    profile_photo: Optional[str] = None
    author: str

    class Config:
        orm_mode = True

class ChatBase(BaseModel):
    participants: List[int]

class ChatCreate(ChatBase):
    pass

class ChatParticipant(BaseModel):
    user: Optional[UserShema] = None




class Chat(ChatBase):
    id: int
    messages: List[Message] = []
    participants: List[ChatParticipant] = None
    contents: List[Content] = None
    reels: List[VideoReelsSchema] = None
    users: Optional[List[UserShema]] = None
    

    class Config:
        orm_mode = True

    

class SendContentSchema(BaseModel):
    content_id: int
    chat_id: int
    message_for_sending_content: Optional[str] = None

class SendReelsSchema(BaseModel):
    reels_id: int
    chat_id: int
    message_for_sending_content: str = None



class SendUserSchema(BaseModel):
    user_id: int
    chat_id: int


class NotificationResponse(BaseModel):
    id: int = None
    user_id: Optional[int] = None
    sender_id: Optional[int] = None
    created_at: Optional[datetime] = None
    chat_id: Optional[int] = None
    sender: Optional[UserShema] = None
    content: Optional[ContentSchema] = None
    type: Optional[str] = None
    video_reels: Optional[VideoReelsSchema] = None