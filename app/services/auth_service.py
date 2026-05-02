# app/services/auth_service.py
"""
处理用户注册、登录的完整业务逻辑。
"""
from typing import Optional

from fastapi import HTTPException, status

from app.core.security import get_password_hash, verify_password
from app.data_access import user_db
from app.models.user_model import User
from app.schemas.user_schemas import UserCreate


async def register_user(user_in: UserCreate) -> User:
    """
    处理用户注册的业务逻辑。

    Args:
        user_in: 用户注册信息。

    Raises:
        HTTPException: 如果用户邮箱已存在。

    Returns:
        创建成功后的用户对象。
    """
    existing_user = await user_db.get_user_by_email(email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该邮箱已被注册",
        )

    hashed_password = get_password_hash(user_in.password)
    new_user = await user_db.create_user(user_in=user_in, hashed_password=hashed_password)
    return new_user


async def authenticate_user(email: str, password: str) -> Optional[User]:
    """
    验证用户凭证。

    Args:
        email: 用户邮箱。
        password: 用户密码。

    Returns:
        如果凭证有效，返回User对象，否则返回None。
    """
    user = await user_db.get_user_by_email(email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_all_users() -> list:
    """
    获取所有用户列表（用于邀请功能）。

    Returns:
        所有用户的信息列表。
    """
    users = await user_db.get_all_users()
    return users