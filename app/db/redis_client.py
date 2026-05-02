# app/db/redis_client.py
"""
[层] 数据库配置层
[职责] 提供一个全局共享的、可复用的Redis客户端实例。
这遵循了单例模式和连接池的最佳实践，确保整个应用高效、稳定地与Redis交互。
"""
from typing import Optional
import redis.asyncio as redis
from app.core.config import settings

# 全局变量，将在应用生命周期中被初始化
redis_client: Optional[redis.Redis] = None

def get_redis_client() -> redis.Redis:
    """
    依赖注入函数，用于在应用各处安全地获取已初始化的Redis客户端实例。

    Raises:
        RuntimeError: 如果Redis客户端尚未初始化。

    Returns:
        已初始化的Redis客户端实例。
    """
    if redis_client is None:
        raise RuntimeError("Redis client is not initialized.")
    return redis_client

async def init_redis_pool():
    """
    在应用启动时调用的初始化函数。
    创建Redis客户端实例并建立连接。
    """
    global redis_client
    if redis_client is None:
        print("Initializing Redis client...")
        redis_client = redis.from_url(f"redis://{settings.REDIS_HOST}")
        await redis_client.ping()
        print("Redis client initialized successfully.")

async def close_redis_pool():
    """
    在应用关闭时调用的关闭函数。
    安全地关闭Redis连接。
    """
    global redis_client
    if redis_client:
        print("Closing Redis client...")
        await redis_client.close()
        redis_client = None
        print("Redis client closed.")