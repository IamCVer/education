# app/data_access/user_db.py
"""
封装所有与MySQL用户表的CRUD操作（使用Tortoise-ORM）。
"""
from typing import Optional, List

from app.models.user_model import User
from app.schemas.user_schemas import UserCreate


async def get_user_by_email(email: str) -> Optional[User]:
    """
    通过邮箱地址查询用户。

    Args:
        email: 用户邮箱地址。

    Returns:
        如果找到，返回User模型实例；否则返回None。
    """
    return await User.get_or_none(email=email)


async def get_user_by_id(user_id: int) -> Optional[User]:
    """
    通过用户ID查询用户。

    Args:
        user_id: 用户ID。

    Returns:
        如果找到，返回User模型实例；否则返回None。
    """
    return await User.get_or_none(id=user_id)


async def get_all_users(skip: int = 0, limit: int = 100) -> List[User]:
    """
    获取所有用户列表（分页）。

    Args:
        skip: 跳过的记录数。
        limit: 返回的最大记录数。

    Returns:
        用户列表。
    """
    return await User.all().offset(skip).limit(limit)


async def create_user(user_in: UserCreate, hashed_password: str) -> User:
    """
    创建一个新用户。

    Args:
        user_in: 包含用户创建信息的Pydantic模型。
        hashed_password: 已经过哈希处理的密码。

    Returns:
        新创建的User模型实例。
    """
    user_obj = User(
        email=user_in.email,
        hashed_password=hashed_password,
        role=user_in.role
    )
    await user_obj.save()
    return user_obj


async def create_user_db(email: str, hashed_password: str, role: str = "user") -> User:
    """
    创建一个新用户（数据库层）。

    Args:
        email: 用户邮箱。
        hashed_password: 已哈希的密码。
        role: 用户角色。

    Returns:
        新创建的User模型实例。
    """
    user_obj = User(
        email=email,
        hashed_password=hashed_password,
        role=role
    )
    await user_obj.save()
    return user_obj


async def update_user_db(user_id: int, email: Optional[str] = None, 
                        hashed_password: Optional[str] = None, 
                        role: Optional[str] = None) -> Optional[User]:
    """
    更新用户信息。

    Args:
        user_id: 用户ID。
        email: 新邮箱（可选）。
        hashed_password: 新密码哈希（可选）。
        role: 新角色（可选）。

    Returns:
        更新后的User模型实例，如果用户不存在则返回None。
    """
    user = await User.get_or_none(id=user_id)
    if not user:
        return None
    
    if email is not None:
        user.email = email
    if hashed_password is not None:
        user.hashed_password = hashed_password
    if role is not None:
        user.role = role
    
    await user.save()
    return user


async def delete_user_db(user_id: int) -> bool:
    """
    删除用户。

    Args:
        user_id: 用户ID。

    Returns:
        如果删除成功返回True，否则返回False。
    """
    user = await User.get_or_none(id=user_id)
    if not user:
        return False
    
    await user.delete()
    return True