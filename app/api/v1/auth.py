# app/api/v1/auth.py
"""
提供用户注册、登录、Token刷新等认证相关的API端点。
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import create_access_token
from app.schemas import token_schemas, user_schemas
from app.services import auth_service
from app.services.notification_service import notify_login
from app.api.deps import get_current_user
from app.models.user_model import User

router = APIRouter()


@router.post("/register", response_model=user_schemas.UserRead)
async def register(user_in: user_schemas.UserCreate):
    """
    处理用户注册请求。

    Args:
        user_in: 用户注册信息。

    Returns:
        新创建的用户信息。
    """
    user = await auth_service.register_user(user_in=user_in)
    return user


@router.post("/login", response_model=token_schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    """
    处理用户登录请求，验证凭证并返回JWT。

    Args:
        form_data: 包含用户名(邮箱)和密码的表单数据。

    Returns:
        包含access_token和token_type的Token对象。
    """
    user = await auth_service.authenticate_user(
        email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # 在请求上下文内同步执行登录通知，避免后台任务中的TortoiseORM上下文问题
    try:
        await notify_login(username=user.email, user_id=user.id)
    except Exception as e:
        # 通知失败不应该影响登录流程
        print(f"Failed to create login notification: {e}")
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=user_schemas.UserRead)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    获取当前登录用户的信息。
    
    用于验证token是否有效，并返回用户基本信息。
    ChatVRM使用此端点验证用户身份。

    Args:
        current_user: 通过JWT token解析出的当前用户。

    Returns:
        当前用户的信息（UserRead格式）。
    """
    return current_user


@router.get("/users/all", response_model=list)
async def get_all_users(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    获取所有用户列表（用于邀请功能）。
    
    返回系统中所有用户的基本信息，用于群聊邀请时选择邀请对象。

    Args:
        current_user: 通过JWT token解析出的当前用户。

    Returns:
        所有用户的信息列表。
    """
    users = await auth_service.get_all_users()
    return [
        {
            "id": user.id,
            "email": user.email,
            "role": user.role
        }
        for user in users
    ]