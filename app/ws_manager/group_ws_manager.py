# app/ws_manager/group_ws_manager.py
"""
[职责] 群组WebSocket连接管理器
"""
from typing import Dict, List, Set
from fastapi import WebSocket
import json


class GroupWSManager:
    """群组WebSocket连接管理器"""
    
    def __init__(self):
        # 存储每个群组的WebSocket连接
        # {group_id: {user_id: websocket}}
        self.active_connections: Dict[str, Dict[int, WebSocket]] = {}
        
        # 存储每个用户当前所在的群组
        # {user_id: group_id}
        self.user_current_group: Dict[int, str] = {}
    
    async def connect(self, group_id: str, user_id: int, websocket: WebSocket):
        """
        用户连接到群组
        
        Args:
            group_id: 群组ID
            user_id: 用户ID
            websocket: WebSocket连接
        """
        await websocket.accept()
        
        # 如果群组不存在，创建新的连接字典
        if group_id not in self.active_connections:
            self.active_connections[group_id] = {}
        
        # 添加用户连接
        self.active_connections[group_id][user_id] = websocket
        self.user_current_group[user_id] = group_id
        
        print(f"User {user_id} connected to group {group_id}")
        
        # 广播用户加入消息
        await self.broadcast(group_id, {
            "type": "member_joined",
            "user_id": user_id,
            "group_id": group_id,
            "online_count": len(self.active_connections[group_id])
        }, exclude_user=user_id)
    
    def disconnect(self, group_id: str, user_id: int):
        """
        用户断开连接
        
        Args:
            group_id: 群组ID
            user_id: 用户ID
        """
        if group_id in self.active_connections:
            if user_id in self.active_connections[group_id]:
                del self.active_connections[group_id][user_id]
                print(f"User {user_id} disconnected from group {group_id}")
                
                # 如果群组没有连接了，删除群组
                if not self.active_connections[group_id]:
                    del self.active_connections[group_id]
        
        if user_id in self.user_current_group:
            del self.user_current_group[user_id]
    
    async def broadcast(self, group_id: str, message: dict, exclude_user: int = None):
        """
        向群组的所有在线成员广播消息
        
        Args:
            group_id: 群组ID
            message: 消息内容（字典）
            exclude_user: 排除的用户ID（可选）
        """
        if group_id not in self.active_connections:
            return
        
        # 需要移除的断开连接
        disconnected_users = []
        
        for user_id, websocket in self.active_connections[group_id].items():
            # 跳过排除的用户
            if exclude_user and user_id == exclude_user:
                continue
            
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # 清理断开的连接
        for user_id in disconnected_users:
            self.disconnect(group_id, user_id)
    
    async def send_to_user(self, group_id: str, user_id: int, message: dict):
        """
        向特定用户发送消息
        
        Args:
            group_id: 群组ID
            user_id: 用户ID
            message: 消息内容
        """
        if group_id in self.active_connections:
            if user_id in self.active_connections[group_id]:
                try:
                    await self.active_connections[group_id][user_id].send_json(message)
                except Exception as e:
                    print(f"Error sending message to user {user_id}: {e}")
                    self.disconnect(group_id, user_id)
    
    def get_online_users(self, group_id: str) -> List[int]:
        """
        获取群组的在线用户列表
        
        Args:
            group_id: 群组ID
        
        Returns:
            在线用户ID列表
        """
        if group_id in self.active_connections:
            return list(self.active_connections[group_id].keys())
        return []
    
    def get_online_count(self, group_id: str) -> int:
        """
        获取群组的在线人数
        
        Args:
            group_id: 群组ID
        
        Returns:
            在线人数
        """
        if group_id in self.active_connections:
            return len(self.active_connections[group_id])
        return 0
    
    def is_user_online(self, group_id: str, user_id: int) -> bool:
        """
        检查用户是否在线
        
        Args:
            group_id: 群组ID
            user_id: 用户ID
        
        Returns:
            是否在线
        """
        if group_id in self.active_connections:
            return user_id in self.active_connections[group_id]
        return False


# 创建全局实例
group_ws_manager = GroupWSManager()
