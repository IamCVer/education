"""
通知相关的 Pydantic Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NotificationBase(BaseModel):
    """通知基础模型"""
    type: str
    title: str
    message: str
    level: str = "info"  # success, info, warning, danger


class NotificationCreate(NotificationBase):
    """创建通知"""
    user_id: Optional[int] = None
    username: Optional[str] = None


class NotificationUpdate(BaseModel):
    """更新通知"""
    is_read: Optional[bool] = None


class NotificationResponse(NotificationBase):
    """通知响应"""
    id: int
    user_id: Optional[int]
    username: Optional[str]
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """通知列表响应"""
    items: list[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int
    total_pages: int


class NotificationStats(BaseModel):
    """通知统计"""
    total: int
    unread: int
    today: int

