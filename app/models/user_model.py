# app/models/user_model.py
"""
定义用户相关的数据库模型 (Tortoise-ORM)。
"""
from enum import Enum

from tortoise import fields
from tortoise.models import Model


class UserRole(str, Enum):
    """用户角色枚举"""
    STUDENT = "student"
    ADMIN = "admin"
    TEACHER = "teacher"


class User(Model):
    """
    用户表模型。
    """
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=255, unique=True, index=True)
    hashed_password = fields.CharField(max_length=255)
    role = fields.CharEnumField(UserRole, default=UserRole.STUDENT)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"

    def __str__(self):
        return self.email