from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, func, Boolean
from sqlalchemy.orm import relationship,  mapped_column, Mapped
from datetime import datetime, timedelta
from .database import Base



content_likes = Table(
    'content_likes', Base.metadata,
    Column('content_id', Integer, ForeignKey('content.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
)



reels_likes = Table(
    'video_reels_likes', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('reels_id', Integer, ForeignKey('video_reels.id', ondelete=('CASCADE')), primary_key=True)
)

chosen = Table(
    'user_chosens', Base.metadata,
    Column('content_id', ForeignKey('content.id'), primary_key=True),
    Column('user_id', ForeignKey('users.id'), primary_key=True)
)

history_likes = Table(
    'history_likes', Base.metadata,
    Column('history_id', Integer, ForeignKey('history.id', ondelete=('CASCADE')), primary_key=True),
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
    Column('reels_id', Integer, ForeignKey('video_reels.id'), nullable=True, primary_key=True),
    Column('content_id', Integer, ForeignKey('content.id'), primary_key=True, nullable=True),
    Column('users_id', Integer, ForeignKey('users.id'), primary_key=True, nullable=True)
)


class Chat(Base):
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    participants: Mapped[list["ChatParticipant"]] = relationship("ChatParticipant", back_populates="chat")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="chat")
    author: Mapped["User"] = relationship('User', back_populates='chat_author')
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    # chat_name: Mapped[str] = mapped_column(String, nullable=True)

    user_content: Mapped[list["Content"]] = relationship(
        'Content',
        secondary=chat_user_content,
        back_populates='chats'
    )

    
    user_reels: Mapped[list["Reels"]] = relationship(
        'Reels',
        secondary=chat_user_content,
        back_populates='chats'
    )

    sended_users: Mapped[list["User"]] = relationship('User', secondary=chat_user_content, back_populates='chats')

    
    user_chat: Mapped[list["UserContent"]] = relationship(
        'UserContent',
        primaryjoin="Chat.id == UserContent.chat_id",
        back_populates='chat'
    )



class UserContent(Base):
    __tablename__ = 'user_content'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    recipient_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    content_id: Mapped[int] = mapped_column(Integer, ForeignKey('content.id'), nullable=True)
    reels_id: Mapped[int] = mapped_column(Integer, ForeignKey('video_reels.id'), nullable=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey('chats.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    users_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)

    sender: Mapped["User"] = relationship('User', foreign_keys=[sender_id], back_populates='sent_content')
    recipient: Mapped["User"] = relationship('User', foreign_keys=[recipient_id], back_populates='received_content')
    content: Mapped["Content"] = relationship('Content', back_populates='user_contents')
    reels: Mapped['Reels'] = relationship('Reels', back_populates='user_reels')
    chat: Mapped["Chat"] = relationship('Chat', primaryjoin="UserContent.chat_id == Chat.id", back_populates='user_chat')

    users: Mapped['User'] = relationship('User', foreign_keys=[users_id], back_populates='sended_users')
    message_for_sending_content: Mapped[str] = mapped_column(String, nullable=True)


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
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    profile_photo = Column(String, nullable=True)
    name = Column(String, nullable=True)
    surname = Column(String, nullable=True)
    bigraph = Column(String, nullable=True)
    birthday_date = Column(DateTime, nullable=True)
    prime_version = Column(Boolean, default=False)
    creation_account_for = Column(String, nullable=True)
    is_closed = Column(Boolean, default=False)

    sent_content = relationship('UserContent', foreign_keys='UserContent.sender_id', back_populates='sender')
    received_content = relationship('UserContent', foreign_keys='UserContent.recipient_id', back_populates='recipient')
    content = relationship('Content', back_populates='author')
    messages = relationship("Message", back_populates="author")
    chat_participants = relationship("ChatParticipant", back_populates="user")
    liked_content = relationship('Content', secondary='content_likes', back_populates='liked_by')
    reset_tokens = relationship("PasswordResetToken", back_populates="user")
    liked_stories = relationship('History', back_populates='liked_by', secondary='history_likes')
    histories = relationship('History', back_populates='author')
    following = relationship(
        'User',
        secondary='subscription',
        primaryjoin='User.id==subscription.c.followed_id',
        secondaryjoin='User.id==subscription.c.follower_id',
        backref='followed_by'
    )
    chat_author = relationship('Chat', back_populates='author')
    commentarion = relationship('CommentarionModel', back_populates='user')
    views = relationship("View", back_populates="user", cascade="all, delete-orphan")
    todo = relationship('UserToDo', back_populates='user')
    user_chosen = relationship('Content', secondary=chosen, back_populates='user_chosen')
    
    reels: Mapped[list['Reels']] = relationship('Reels', back_populates='user')

    liked_reels = relationship('Reels', secondary='video_reels_likes', back_populates='liked_by', cascade='all')

    sended_users: Mapped['UserContent'] = relationship('UserContent', back_populates='users', foreign_keys=[UserContent.sender_id])

    chats: Mapped["Chat"] = relationship('Chat', back_populates='sended_users')

class ChatParticipant(Base):
    __tablename__ = 'chat_participants'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey('chats.id'), nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))

    chat: Mapped["Chat"] = relationship("Chat", back_populates="participants")
    user: Mapped["User"] = relationship("User", back_populates="chat_participants")

class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message: Mapped[str] = mapped_column(String)
    img_file: Mapped[str] = mapped_column(String, nullable=True)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey('chats.id'), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow())

    author: Mapped["User"] = relationship("User", back_populates="messages")
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")
    is_updated : Mapped[Boolean] = mapped_column(Boolean, nullable=True, default=False)
    

class Content(Base):
    __tablename__ = 'content'

    id: Mapped[int] = mapped_column(Integer, index=True, primary_key=True)
    content_title: Mapped[str] = mapped_column(String, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    liked_by: Mapped[list["User"]] = relationship('User', secondary=history_likes, back_populates='liked_stories')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow())
    delete_at: Mapped[datetime] = mapped_column(DateTime, default= lambda: datetime.utcnow() + timedelta(days=1))

    author: Mapped["User"] = relationship('User', back_populates='histories')
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))  # Убрано primary_key=True
    views: Mapped[list["View"]] = relationship('View', back_populates='history', cascade='all, delete-orphan')
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    who_viewed: Mapped["View"] = relationship('View', cascade='all, delete-orphan')
    who_liked: Mapped["User"] = relationship('User', secondary=history_likes)



class CommentarionModel(Base):
    __tablename__ = 'commentarion_model'

    id: Mapped[int] = mapped_column(Integer, index=True, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content_id: Mapped[int] = mapped_column(Integer, ForeignKey('content.id'), nullable=True)
    reels_id: Mapped[int] = mapped_column(Integer, ForeignKey('video_reels.id'), nullable=True)
    
    content: Mapped["Content"] = relationship('Content', back_populates='commentarion')
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    user: Mapped["User"] = relationship('User', back_populates='commentarion')
    date_pub: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow())

class View(Base):
    __tablename__ = 'views'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content_id: Mapped[int] = mapped_column(Integer, ForeignKey('content.id'), index=True, nullable=True)
    history_id: Mapped[int] = mapped_column(Integer, ForeignKey('history.id', ondelete=('CASCADE')), index=True, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), index=True, nullable=True)
    reels_id: Mapped[int]= mapped_column(Integer, ForeignKey('video_reels.id'), index=True, nullable=True)
    viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    content: Mapped["Content"] = relationship("Content", back_populates="views")
    history: Mapped["History"] = relationship('History', back_populates='views')
    user: Mapped["User"] = relationship("User", back_populates="views")
    reels: Mapped["Reels"] = relationship("Reels", back_populates="views")


class UserToDo(Base):
    __tablename__ = 'user_todo'

    id: Mapped[int] = mapped_column(Integer, index=True, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow())
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    user: Mapped["User"] = relationship("User", back_populates="todo", foreign_keys=[user_id])

    title: Mapped[str] = mapped_column(String, nullable=False)
    file: Mapped[str] = mapped_column(String, nullable=True)



class Reels(Base):
    __tablename__ = 'video_reels'

    id: Mapped[int] = mapped_column(Integer, index=True, primary_key=True)

    reels_title: Mapped[str] = mapped_column(String, nullable=False)
    video_reels: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow())
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    user: Mapped['User'] = relationship('User', back_populates='reels')

    views: Mapped[list["View"]] = relationship("View", back_populates="reels", cascade="all, delete-orphan")
    who_viewed: Mapped["View"] = relationship("View" , cascade="all, delete-orphan")
    
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    
    liked_by: Mapped[list["User"]] = relationship('User', secondary=reels_likes,  back_populates='liked_reels')
    
    who_liked: Mapped["User"] = relationship('User', secondary=reels_likes)

    place: Mapped[str] = mapped_column(String, nullable=True)
    comments: Mapped[list['CommentarionModel']] = relationship('CommentarionModel')

    user_reels: Mapped[list['UserContent']] = relationship('UserContent', back_populates='reels')
    chats: Mapped['Chat'] = relationship('Chat', secondary=chat_user_content, back_populates='user_reels')



class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    content_id: Mapped[int] = mapped_column(Integer, ForeignKey('content.id', ondelete=('CASCADE')), nullable=True)
    video_reels_id: Mapped[int] = mapped_column(Integer, ForeignKey('video_reels.id'),  nullable=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped['User'] = relationship("User", foreign_keys=[user_id])
    sender: Mapped['User'] = relationship("User", foreign_keys=[sender_id])
    
    content: Mapped['Content'] = relationship('Content')
    video_reels: Mapped['Reels'] = relationship('Reels')


    video_reels_len: Mapped[list['Reels']] = relationship('Reels')
    content_len: Mapped[list['Content']] = relationship('Content')