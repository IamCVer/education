"""
通知服务
用于创建和管理系统通知
"""
from datetime import datetime, timedelta
from typing import Optional
from app.models.notification_model import Notification


class NotificationService:
    """通知服务类"""
    
    @staticmethod
    async def create_notification(
        type: str,
        title: str,
        message: str,
        level: str = "info",
        user_id: Optional[int] = None,
        username: Optional[str] = None
    ) -> Notification:
        """
        创建通知
        
        Args:
            type: 通知类型（login, logout, password_change, export, import等）
            title: 通知标题
            message: 通知内容
            level: 通知级别（success, info, warning, danger）
            user_id: 用户ID（可选）
            username: 用户名（可选）
        
        Returns:
            Notification: 创建的通知对象
        """
        notification = await Notification.create(
            user_id=user_id,
            username=username,
            type=type,
            title=title,
            message=message,
            level=level
        )
        return notification
    
    @staticmethod
    async def get_notifications(
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[int] = None,
        is_read: Optional[bool] = None
    ):
        """
        获取通知列表
        
        Args:
            page: 页码
            page_size: 每页数量
            user_id: 用户ID（可选，筛选特定用户的通知）
            is_read: 是否已读（可选，筛选已读/未读）
        
        Returns:
            tuple: (通知列表, 总数, 未读数)
        """
        query = Notification.all()
        
        # 筛选条件
        if user_id is not None:
            query = query.filter(user_id=user_id)
        
        if is_read is not None:
            query = query.filter(is_read=is_read)
        
        # 获取总数和未读数
        total = await query.count()
        unread_query = Notification.filter(is_read=False)
        if user_id is not None:
            unread_query = unread_query.filter(user_id=user_id)
        unread_count = await unread_query.count()
        
        # 分页
        offset = (page - 1) * page_size
        notifications = await query.offset(offset).limit(page_size)
        
        return notifications, total, unread_count
    
    @staticmethod
    async def mark_as_read(notification_id: int) -> bool:
        """
        标记通知为已读
        
        Args:
            notification_id: 通知ID
        
        Returns:
            bool: 是否成功
        """
        notification = await Notification.get_or_none(id=notification_id)
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now()
            await notification.save()
            return True
        return False
    
    @staticmethod
    async def mark_all_as_read(user_id: Optional[int] = None) -> int:
        """
        标记所有通知为已读
        
        Args:
            user_id: 用户ID（可选，只标记特定用户的通知）
        
        Returns:
            int: 标记的数量
        """
        query = Notification.filter(is_read=False)
        if user_id is not None:
            query = query.filter(user_id=user_id)
        
        count = await query.update(is_read=True, read_at=datetime.now())
        return count
    
    @staticmethod
    async def delete_notification(notification_id: int) -> bool:
        """
        删除通知
        
        Args:
            notification_id: 通知ID
        
        Returns:
            bool: 是否成功
        """
        notification = await Notification.get_or_none(id=notification_id)
        if notification:
            await notification.delete()
            return True
        return False
    
    @staticmethod
    async def get_notification_stats(user_id: Optional[int] = None):
        """
        获取通知统计
        
        Args:
            user_id: 用户ID（可选）
        
        Returns:
            dict: 统计信息
        """
        query = Notification.all()
        if user_id is not None:
            query = query.filter(user_id=user_id)
        
        total = await query.count()
        unread = await query.filter(is_read=False).count()
        
        # 今天的通知
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today = await query.filter(created_at__gte=today_start).count()
        
        return {
            "total": total,
            "unread": unread,
            "today": today
        }


# 便捷函数
async def notify_login(username: str, user_id: int, ip: str = ""):
    """用户登录通知"""
    return await NotificationService.create_notification(
        type="login",
        title="登录成功",
        message=f"用户 {username} 于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 登录系统" + (f"，IP: {ip}" if ip else ""),
        level="success",
        user_id=user_id,
        username=username
    )


async def notify_logout(username: str, user_id: int):
    """用户登出通知"""
    return await NotificationService.create_notification(
        type="logout",
        title="登出成功",
        message=f"用户 {username} 于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 登出系统",
        level="info",
        user_id=user_id,
        username=username
    )


async def notify_password_change(username: str, user_id: int):
    """密码修改通知"""
    return await NotificationService.create_notification(
        type="password_change",
        title="密码修改成功",
        message=f"用户 {username} 于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 成功修改密码",
        level="warning",
        user_id=user_id,
        username=username
    )


async def notify_data_export(username: str, user_id: int, data_type: str):
    """数据导出通知"""
    return await NotificationService.create_notification(
        type="export",
        title="数据导出成功",
        message=f"用户 {username} 于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 成功导出{data_type}数据",
        level="success",
        user_id=user_id,
        username=username
    )


async def notify_data_import(username: str, user_id: int, filename: str, success: bool = True):
    """数据导入通知"""
    if success:
        return await NotificationService.create_notification(
            type="import",
            title="数据导入成功",
            message=f"用户 {username} 于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 成功导入文件 {filename}",
            level="success",
            user_id=user_id,
            username=username
        )
    else:
        return await NotificationService.create_notification(
            type="import",
            title="数据导入失败",
            message=f"用户 {username} 于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 导入文件 {filename} 失败",
            level="danger",
            user_id=user_id,
            username=username
        )


async def notify_system(title: str, message: str, level: str = "info"):
    """系统通知"""
    return await NotificationService.create_notification(
        type="system",
        title=title,
        message=message,
        level=level
    )


async def notify_pending_invitation(teacher_id: int, group_name: str, inviter_name: str, invited_user_name: str, reason: str):
    """待审核邀请通知"""
    return await NotificationService.create_notification(
        type="pending_invitation",
        title="新的邀请待审核",
        message=f"群聊 '{group_name}' 中，学生 {inviter_name} 邀请 {invited_user_name} 加入，理由：{reason}",
        level="warning",
        user_id=teacher_id
    )

