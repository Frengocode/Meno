from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, func, Boolean
from sqlalchemy.orm import relationship,  mapped_column, Mapped
from datetime import datetime, timedelta
from .database import Base



content_likes = Table(
    'content_likes', Base.metadata,
    Column('content_id', Integer, ForeignKey('content.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('stories_id', Integer, ForeignKey('history.id'), primary_key=True)
)

chosen = Table(
    'user_chosens', Base.metadata,
    Column('content_id', ForeignKey('content.id'), primary_key=True),
    Column('user_id', ForeignKey('users.id'), primary_key=True)
)

history_likes = Table(
    'history_likes', Base.metadata,
    Column('history_id', Integer, ForeignKey('history.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)

subscription = Table(
    'subscription', Base.metadata,
    Column('follower_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('followed_id', Integer, ForeignKey('users.id'), primary_key=True)
)

chat_user_content = Table(
    'chat_user_content', Base.metadata,
    Column('chat_id', Integer, ForeignKey('chats.id'), primary_key=True),
    Column('content_id', Integer, ForeignKey('content.id'), primary_key=True)
)

class Chat(Base):
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    participants: Mapped[list["ChatParticipant"]] = relationship("ChatParticipant", back_populates="chat")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="chat")
    author: Mapped["User"] = relationship('User', back_populates='chat_author')
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))

    user_content: Mapped[list["Content"]] = relationship(
        'Content',
        secondary=chat_user_content,
        back_populates='chats'
    )
    
    user_chat: Mapped[list["UserContent"]] = relationship(
        'UserContent',
        primaryjoin="Chat.id == UserContent.chat_id",
        back_populates='chat'
    )

class UserContent(Base):
    __tablename__ = 'user_content'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    recipient_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    content_id: Mapped[int] = mapped_column(Integer, ForeignKey('content.id'), nullable=False)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey('chats.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    sender: Mapped["User"] = relationship('User', foreign_keys=[sender_id], back_populates='sent_content')
    recipient: Mapped["User"] = relationship('User', foreign_keys=[recipient_id], back_populates='received_content')
    content: Mapped["Content"] = relationship('Content', back_populates='user_contents')
    chat: Mapped["Chat"] = relationship('Chat', primaryjoin="UserContent.chat_id == Chat.id", back_populates='user_chat')

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=1))
    user: Mapped["User"] = relationship("User", back_populates="reset_tokens")

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    profile_photo: Mapped[str] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    surname: Mapped[str] = mapped_column(String, nullable=False)
    bigraph : Mapped[str] = mapped_column(String, nullable=True)
    birthday_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    prime_version: Mapped[bool] = mapped_column(Boolean, default=False)

    # All relationship and foreign_keys
   
    sent_content: Mapped[list["UserContent"]] = relationship('UserContent', foreign_keys=[UserContent.sender_id], back_populates='sender')
    received_content: Mapped[list["UserContent"]] = relationship('UserContent', foreign_keys=[UserContent.recipient_id], back_populates='recipient')
    content: Mapped[list["Content"]] = relationship('Content', back_populates='author')
   
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="author")
    chat_participants: Mapped[list["ChatParticipant"]] = relationship("ChatParticipant", back_populates="user")
    liked_content: Mapped[list["Content"]] = relationship('Content', secondary='content_likes', back_populates='liked_by')
    
    reset_tokens: Mapped[list["PasswordResetToken"]] = relationship("PasswordResetToken", back_populates="user")
    liked_stories: Mapped[list["History"]] = relationship('History', back_populates='liked_by', secondary='history_likes')
    histories: Mapped[list["History"]] = relationship('History', back_populates='author')


    following: Mapped[list["User"]] = relationship(
        'User',
        secondary=subscription,
        primaryjoin=id==subscription.c.followed_id,
        secondaryjoin=id==subscription.c.follower_id,
        backref='followed_by'
    )

    chat_author: Mapped[list["Chat"]] = relationship('Chat', back_populates='author')
    commentarion: Mapped[list["CommentarionModel"]] = relationship('CommentarionModel', back_populates='user')

    views: Mapped[list["View"]] = relationship("View", back_populates="user", cascade="all, delete-orphan")
    todo: Mapped[list["UserToDo"]] = relationship('UserToDo', back_populates='user')

    user_chosen: Mapped[list["Content"]] = relationship('Content', secondary=chosen, back_populates='user_chosen')
    creation_account_for : Mapped[str] = mapped_column(String, nullable=False)


    @classmethod
    def __init__(self, username, email, password, profile_photo=None, name=None, surname=None, birthday_date=None, prime_version=False, creation_account_for=None):
        self.username = username
        self.email = email
        self.password = password
        self.profile_photo = profile_photo
        self.name = name
        self.surname = surname
        self.birthday_date = birthday_date
        self.prime_version = prime_version
        self.creation_account_for = creation_account_for.value  


class ChatParticipant(Base):
    __tablename__ = 'chat_participants'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey('chats.id'))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))

    chat: Mapped["Chat"] = relationship("Chat", back_populates="participants")
    user: Mapped["User"] = relationship("User", back_populates="chat_participants")

class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message: Mapped[str] = mapped_column(String)
    img_file: Mapped[str] = mapped_column(String, nullable=True)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey('chats.id'))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow())

    author: Mapped["User"] = relationship("User", back_populates="messages")
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")
    is_updated : Mapped[Boolean] = mapped_column(Boolean, nullable=True, default=False)
    

class Content(Base):
    __tablename__ = 'content'

    id: Mapped[int] = mapped_column(Integer, index=True, primary_key=True)
    content_title: Mapped[str] = mapped_column(String, nullable=False)
    
    content_photo: Mapped[str] = mapped_column(String, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    author: Mapped["User"] = relationship('User', back_populates='content')
    liked_by: Mapped[list["User"]] = relationship('User', secondary=content_likes, back_populates='liked_content')
    user_contents: Mapped[list["UserContent"]] = relationship('UserContent', back_populates='content')
    
    chats: Mapped[list["Chat"]] = relationship('Chat', secondary=chat_user_content, back_populates='user_content')
    commentarion: Mapped[list["CommentarionModel"]] = relationship('CommentarionModel', back_populates='content')
    views: Mapped[list["View"]] = relationship("View", back_populates="content", cascade="all, delete-orphan")
    
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    user_chosen: Mapped[list["User"]] = relationship('User', secondary=chosen, back_populates='user_chosen')
    content_for : Mapped[str] = mapped_column(String, nullable=False)


    def __init__(self, content_title = None, content_photo = None, created_at = None, author_id = None, content_for = None):
        
        self.content_title = content_title
        self.content_photo = content_photo
        self.created_at = created_at
        self.author_id = author_id
        self.content_for = content_for.value
        



class History(Base):
    __tablename__ = 'history'

    id: Mapped[int] = mapped_column(Integer, index=True, primary_key=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    liked_by: Mapped[list["User"]] = relationship('User', secondary=history_likes, back_populates='liked_stories')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow())
    delete_at: Mapped[datetime] = mapped_column(DateTime, default= lambda: datetime.utcnow() + timedelta(days=1))

    author: Mapped["User"] = relationship('User', back_populates='histories')
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), primary_key=True)
    views: Mapped[list["View"]] = relationship('View', back_populates='history')
    views_count: Mapped[int] = mapped_column(Integer, default=0)

class CommentarionModel(Base):
    __tablename__ = 'commentarion_model'

    id: Mapped[int] = mapped_column(Integer, index=True, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content_id: Mapped[int] = mapped_column(Integer, ForeignKey('content.id'))
    
    content: Mapped["Content"] = relationship('Content', back_populates='commentarion')
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    user: Mapped["User"] = relationship('User', back_populates='commentarion')
    date_pub: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow())

class View(Base):
    __tablename__ = 'views'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content_id: Mapped[int] = mapped_column(Integer, ForeignKey('content.id'), index=True)
    history_id: Mapped[int] = mapped_column(Integer, ForeignKey('history.id'), index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), index=True, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    content: Mapped["Content"] = relationship("Content", back_populates="views")
    history: Mapped["History"] = relationship('History', back_populates='views')
    user: Mapped["User"] = relationship("User", back_populates="views")

class UserToDo(Base):
    __tablename__ = 'user_todo'

    id: Mapped[int] = mapped_column(Integer, index=True, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow())
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    user: Mapped["User"] = relationship("User", back_populates="todo", foreign_keys=[user_id])

    title: Mapped[str] = mapped_column(String, nullable=False)
    file: Mapped[str] = mapped_column(String, nullable=True)
