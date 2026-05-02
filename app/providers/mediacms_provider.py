"""
MediaCMS服务提供者

封装与MediaCMS的HTTP通信，提供视频上传、管理等功能
"""

import httpx
from typing import Optional, Dict, Any
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class MediaCMSProvider:
    """MediaCMS服务提供者类"""
    
    def __init__(self):
        self.base_url = settings.mediacms_url
        self.api_url = settings.mediacms_api_url
        self.admin_token = settings.mediacms_admin_token
        self.timeout = 300.0  # 5分钟超时（视频上传可能需要较长时间）
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Token {self.admin_token}",
            "Content-Type": "application/json"
        }
    
    async def upload_video(
        self,
        file_path: str,
        title: str,
        description: Optional[str] = None,
        is_public: bool = False
    ) -> Dict[str, Any]:
        """
        上传视频到MediaCMS
        
        Args:
            file_path: 视频文件路径
            title: 视频标题
            description: 视频描述
            is_public: 是否公开
            
        Returns:
            dict: MediaCMS返回的视频信息
            
        Raises:
            httpx.HTTPError: 上传失败时抛出
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 准备multipart表单数据
                with open(file_path, "rb") as f:
                    files = {"media_file": (file_path.split("/")[-1], f, "video/mp4")}
                    data = {
                        "title": title,
                        "description": description or "",
                        "is_public": str(is_public).lower()
                    }
                    
                    headers = {"Authorization": f"Token {self.admin_token}"}
                    
                    response = await client.post(
                        f"{self.api_url}/media",
                        files=files,
                        data=data,
                        headers=headers
                    )
                    response.raise_for_status()
                    return response.json()
        except Exception as e:
            logger.error(f"Failed to upload video to MediaCMS: {str(e)}")
            raise
    
    async def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        获取视频信息
        
        Args:
            video_id: MediaCMS视频ID
            
        Returns:
            dict: 视频信息，如果不存在返回None
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.api_url}/media/{video_id}",
                    headers=self._get_headers()
                )
                
                if response.status_code == 404:
                    return None
                
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get video info from MediaCMS: {str(e)}")
            return None
    
    async def update_video(
        self,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        is_public: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        更新视频信息
        
        Args:
            video_id: MediaCMS视频ID
            title: 新标题
            description: 新描述
            is_public: 是否公开
            
        Returns:
            dict: 更新后的视频信息
        """
        try:
            update_data = {}
            if title is not None:
                update_data["title"] = title
            if description is not None:
                update_data["description"] = description
            if is_public is not None:
                update_data["is_public"] = is_public
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    f"{self.api_url}/media/{video_id}",
                    json=update_data,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to update video in MediaCMS: {str(e)}")
            return None
    
    async def delete_video(self, video_id: str) -> bool:
        """
        删除视频
        
        Args:
            video_id: MediaCMS视频ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.api_url}/media/{video_id}",
                    headers=self._get_headers()
                )
                return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Failed to delete video from MediaCMS: {str(e)}")
            return False
    
    async def get_video_stream_url(self, video_id: str, quality: str = "720p") -> Optional[str]:
        """
        获取视频流URL（HLS）
        
        Args:
            video_id: MediaCMS视频ID
            quality: 视频质量（720p, 1080p等）
            
        Returns:
            str: HLS流URL
        """
        video_info = await self.get_video_info(video_id)
        if not video_info:
            return None
        
        # MediaCMS通常会提供encodings字段，包含不同质量的视频URL
        encodings = video_info.get("encodings", [])
        for encoding in encodings:
            if encoding.get("resolution") == quality:
                return encoding.get("url")
        
        # 如果没有找到指定质量，返回第一个可用的
        if encodings:
            return encodings[0].get("url")
        
        return None
    
    async def get_video_thumbnail(self, video_id: str) -> Optional[str]:
        """
        获取视频缩略图URL
        
        Args:
            video_id: MediaCMS视频ID
            
        Returns:
            str: 缩略图URL
        """
        video_info = await self.get_video_info(video_id)
        if not video_info:
            return None
        
        return video_info.get("thumbnail_url") or video_info.get("poster_url")
    
    async def check_processing_status(self, video_id: str) -> Dict[str, Any]:
        """
        检查视频处理状态
        
        Args:
            video_id: MediaCMS视频ID
            
        Returns:
            dict: {"status": str, "progress": int, "message": str}
        """
        video_info = await self.get_video_info(video_id)
        if not video_info:
            return {"status": "failed", "progress": 0, "message": "Video not found"}
        
        # MediaCMS的状态字段可能是state或status
        state = video_info.get("state") or video_info.get("status", "unknown")
        
        # 映射MediaCMS状态到我们的状态
        status_mapping = {
            "pending": "processing",
            "running": "processing",
            "success": "ready",
            "fail": "failed",
            "error": "failed"
        }
        
        our_status = status_mapping.get(state, "processing")
        progress = video_info.get("encoding_progress", 0)
        
        return {
            "status": our_status,
            "progress": progress,
            "message": video_info.get("encoding_status", "")
        }


# 创建全局实例
mediacms_provider = MediaCMSProvider()
