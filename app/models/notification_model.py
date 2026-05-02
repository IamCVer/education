"""
通知模型
"""
from tortoise import fields
from tortoise.models import Model


class Notification(Model):
    """通知记录表"""
    
    id = fields.IntField(pk=True)
    user_id = fields.IntField(null=True, description="用户ID，为空表示系统通知")
    username = fields.CharField(max_length=100, null=True, description="用户名")
    type = fields.CharField(max_length=50, description="通知类型：login/logout/password_change/export/import/etc")
    title = fields.CharField(max_length=200, description="通知标题")
    message = fields.TextField(description="通知内容")
    level = fields.CharField(max_length=20, default="info", description="通知级别：success/info/warning/danger")
    is_read = fields.BooleanField(default=False, description="是否已读")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    read_at = fields.DatetimeField(null=True, description="阅读时间")
    
    class Meta:
        table = "notifications"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.username or 'System'} - {self.title}"

