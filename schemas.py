from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Авторизація ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- Коментарі ---
class CommentBase(BaseModel):
    text: str

class CommentCreate(CommentBase):
    post_id: int

class Comment(CommentBase):
    id: int
    post_id: int
    owner_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- Пости ---
class PostBase(BaseModel):
    title: str
    content: str

class PostCreate(PostBase):
    pass

class Post(PostBase):
    id: int
    owner_id: int
    created_at: datetime
    comments: List[Comment] = []  # Вкладені коментарі!
    class Config:
        from_attributes = True

# --- Користувачі ---
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    posts: List[Post] = []
    class Config:
        from_attributes = True


class PostUpdate(BaseModel):
    title: str
    content: str