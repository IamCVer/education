# app/schemas/user_schemas.py
"""
定义UserCreate, UserRead等与用户相关的Pydantic模型。
"""
from pydantic import BaseModel, EmailStr

from app.models.user_model import UserRole


class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr
    role: UserRole = UserRole.STUDENT


class UserCreate(UserBase):
    """用户创建模型"""
    password: str


class UserRead(UserBase):
    """用户读取模型 (用于API响应)"""
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class UserInDB(UserBase):
    """数据库中的用户模型 (包含哈希密码)"""
    id: int
    hashed_password: str