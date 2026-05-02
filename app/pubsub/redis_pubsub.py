# app/pubsub/redis_pubsub.py
"""
[层] 实时消息层
[职责] 封装Redis Pub/Sub的发布和订阅逻辑，并内置无限重连机制以确保高可用性。
"""
import asyncio
import json
import sys
from typing import Callable

from app.db.redis_client import get_redis_client  # 导入中央客户端
from app.ws_manager.connection_manager import manager

CHANNEL_NAME = "qa_results"


async def publish_message(message: dict):
    """
    发布消息到Redis频道。
    现在从中央客户端获取连接，不再自己创建和关闭。

    Args:
        message: 需要发布的消息字典。
    """
    try:
        redis_client = get_redis_client()
        await redis_client.publish(CHANNEL_NAME, json.dumps(message))
    except Exception as e:
        print(f"Error publishing Redis message: {e}", file=sys.stderr, flush=True)


async def message_handler(data: dict):
    """
    默认的消息处理器，用于将结果通过WebSocket推送给用户。

    Args:
        data: 从Redis频道接收到的消息字典。
    """
    user_id = data.get("user_id")
    payload = data.get("payload")
    if user_id and payload:
        await manager.send_personal_message(payload, user_id)
        print(f"---PUBSUB: Message sent to user_id: {user_id} via WebSocket---", file=sys.stderr, flush=True)


async def robust_subscriber(handler: Callable):
    """
    一个健壮的、带无限重连逻辑的Redis频道订阅者。

    Args:
        handler: 用于处理接收到的消息的回调函数。
    """
    while True:
        try:
            print("---PUBSUB: Attempting to connect and subscribe to Redis channel...---", file=sys.stderr, flush=True)
            redis_client = get_redis_client()
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(CHANNEL_NAME)
            print(f"---PUBSUB: Successfully subscribed to channel '{CHANNEL_NAME}'. Listening for messages...---",
                  file=sys.stderr, flush=True)

            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "message":
                    data = json.loads(message["data"])
                    await handler(data)

        except asyncio.CancelledError:
            print("---PUBSUB: Subscriber task cancelled. Shutting down...---", file=sys.stderr, flush=True)
            break
        except Exception as e:
            print(f"---PUBSUB ERROR: Lost connection to Redis or other error: {e}. Reconnecting in 5 seconds...---",
                  file=sys.stderr, flush=True)
            await asyncio.sleep(5)  # 等待5秒后重连