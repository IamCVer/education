# app/core/security.py
"""
封装所有与安全相关的功能，包括密码哈希与验证、JWT Token的生成与解码。
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# 使用Bcrypt算法进行密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与哈希密码是否匹配。

    Args:
        plain_password: 用户提交的明文密码。
        hashed_password: 数据库中存储的哈希密码。

    Returns:
        如果密码匹配则返回True，否则返回False。
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    对明文密码进行哈希加密。

    Args:
        password: 需要加密的明文密码。

    Returns:
        加密后的哈希密码字符串。
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    生成JWT访问令牌。

    Args:
        data: 需要编码到Token中的数据 (payload)。
        expires_delta: Token的过期时间增量。如果为None，则使用默认配置。

    Returns:
        编码后的JWT字符串。
    """
    to_encode: dict[str, Any] = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> dict | None:
    """
    验证JWT Token并返回Payload
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None