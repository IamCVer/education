"""
通知管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.models.user_model import User, UserRole
from app.api.deps import get_current_user
from app.schemas.notification_schemas import (
    NotificationResponse,
    NotificationListResponse,
    NotificationStats,
    NotificationUpdate
)
from app.services.notification_service import NotificationService
from app.models.notification_model import Notification

router = APIRouter()


@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_read: Optional[bool] = Query(None, description="筛选已读/未读"),
    current_user: User = Depends(get_current_user)
):
    """
    获取通知列表（分页）
    """
    # 管理员可以看到所有通知，普通用户只能看到自己的通知
    user_id = None if current_user.role == UserRole.ADMIN else current_user.id
    
    notifications, total, unread_count = await NotificationService.get_notifications(
        page=page,
        page_size=page_size,
        user_id=user_id,
        is_read=is_read
    )
    
    # 转换为响应模型
    items = []
    for notification in notifications:
        items.append(NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            username=notification.username,
            type=notification.type,
            title=notification.title,
            message=notification.message,
            level=notification.level,
            is_read=notification.is_read,
            created_at=notification.created_at,
            read_at=notification.read_at
        ))
    
    total_pages = (total + page_size - 1) // page_size
    
    return NotificationListResponse(
        items=items,
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/notifications/stats", response_model=NotificationStats)
async def get_notification_stats(
    current_user: User = Depends(get_current_user)
):
    """
    获取通知统计信息
    """
    user_id = None if current_user.role == UserRole.ADMIN else current_user.id
    stats = await NotificationService.get_notification_stats(user_id=user_id)
    
    return NotificationStats(**stats)


@router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    标记单个通知为已读
    """
    notification = await Notification.get_or_none(id=notification_id)
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 检查权限：管理员可以标记所有通知，普通用户只能标记自己的通知
    if current_user.role != UserRole.ADMIN and notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限操作此通知")
    
    success = await NotificationService.mark_as_read(notification_id)
    
    if success:
        return {"message": "已标记为已读"}
    else:
        return {"message": "通知已经是已读状态"}


@router.put("/notifications/read-all")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user)
):
    """
    标记所有通知为已读
    """
    user_id = None if current_user.role == UserRole.ADMIN else current_user.id
    count = await NotificationService.mark_all_as_read(user_id=user_id)
    
    return {"message": f"已标记 {count} 条通知为已读"}


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    删除通知
    """
    notification = await Notification.get_or_none(id=notification_id)
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 检查权限：管理员可以删除所有通知，普通用户只能删除自己的通知
    if current_user.role != UserRole.ADMIN and notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限操作此通知")
    
    success = await NotificationService.delete_notification(notification_id)
    
    if success:
        return {"message": "通知已删除"}
    else:
        raise HTTPException(status_code=404, detail="通知不存在")

