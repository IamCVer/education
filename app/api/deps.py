# app/api/deps.py (最终正确版)
"""
定义FastAPI的依赖注入函数，用于实现用户认证和权限检查。
"""
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import ValidationError
# vvvvvvvvvvvv 【核心修正：导入正确的事务管理器】 vvvvvvvvvvvv
from tortoise.transactions import in_transaction
# ^^^^^^^^^^^^ 【核心修正结束】 ^^^^^^^^^^^^

from app.core.config import settings
from app.core.security import jwt
from app.data_access import user_db
from app.models.user_model import User
from app.schemas.token_schemas import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """
    (HTTP专用) 解码并验证JWT，然后从数据库中获取当前用户。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(sub=payload.get("sub"))
        if token_data.sub is None:
            raise credentials_exception
    except (JWTError, ValidationError):
        raise credentials_exception

    # 对于HTTP请求，Tortoise-ORM与FastAPI的集成通常能很好地管理连接，
    # 但为保持一致和绝对稳定，我们同样可以将其包裹在事务中。
    async with in_transaction():
        user = await user_db.get_user_by_id(user_id=int(token_data.sub))

    if user is None:
        raise credentials_exception
    return user


async def get_user_from_token(token: str) -> Optional[User]:
    """
    一个可重用的核心认证函数：解码token并返回User对象。
    如果token无效或用户不存在，则返回 None。
    """
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(sub=payload.get("sub"))
        if token_data.sub is None:
            return None
    except (JWTError, ValidationError):
        return None

    # vvvvvvvvvvvv 【核心修正：使用正确的事务语法】 vvvvvvvvvvvv
    # 显式地开启一个事务，确保在此上下文中数据库连接是可用的
    async with in_transaction():
        user = await user_db.get_user_by_id(user_id=int(token_data.sub))
    # ^^^^^^^^^^^^ 【核心修正结束】 ^^^^^^^^^^^^

    return user


async def get_admin_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """
    验证当前用户是否为管理员。
    
    Args:
        current_user: 当前已认证的用户。
    
    Returns:
        如果是管理员，返回用户对象。
    
    Raises:
        HTTPException: 如果用户不是管理员。
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    return current_user