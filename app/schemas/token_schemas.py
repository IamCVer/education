# app/schemas/token_schemas.py
"""
定义Token响应格式等与JWT相关的Pydantic模型。
"""
from pydantic import BaseModel


class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    """Token载荷模型"""
    sub: str | None = None