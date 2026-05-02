"""
阿里云OSS服务提供者

封装与阿里云对象存储的交互，提供视频文件上传、下载、删除等功能
"""

import oss2
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class OSSProvider:
    """阿里云OSS服务提供者类"""
    
    def __init__(self):
        self.access_key_id = settings.oss_access_key_id
        self.access_key_secret = settings.oss_access_key_secret
        self.endpoint = settings.oss_endpoint
        self.bucket_name = settings.oss_bucket_name
        
        # 初始化OSS认证和Bucket
        auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        self.bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)
    
    def generate_object_key(self, user_id: int, filename: str) -> str:
        """
        生成OSS对象存储Key
        
        Args:
            user_id: 用户ID
            filename: 原始文件名
            
        Returns:
            str: OSS对象Key，格式：videos/{user_id}/{timestamp}_{filename}
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"videos/{user_id}/{timestamp}_{filename}"
    
    async def upload_file(
        self,
        file_path: str,
        object_key: str,
        content_type: str = "video/mp4"
    ) -> Dict[str, Any]:
        """
        上传文件到OSS
        
        Args:
            file_path: 本地文件路径
            object_key: OSS对象Key
            content_type: 文件MIME类型
            
        Returns:
            dict: {"success": bool, "object_key": str, "url": str, "error": str}
        """
        import asyncio
        
        try:
            # 在线程池中执行同步的OSS上传操作
            result = await asyncio.to_thread(
                self.bucket.put_object_from_file,
                object_key,
                file_path,
                headers={"Content-Type": content_type}
            )
            
            # 生成访问URL
            url = self.get_object_url(object_key)
            
            return {
                "success": True,
                "object_key": object_key,
                "url": url,
                "etag": result.etag,
                "error": None
            }
        except Exception as e:
            import traceback
            error_details = {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc()
            }
            logger.error(f"Failed to upload file to OSS: {error_details}")
            return {
                "success": False,
                "object_key": object_key,
                "url": None,
                "error": error_details
            }
    
    async def upload_stream(
        self,
        file_stream: bytes,
        object_key: str,
        content_type: str = "video/mp4"
    ) -> Dict[str, Any]:
        """
        上传文件流到OSS
        
        Args:
            file_stream: 文件字节流
            object_key: OSS对象Key
            content_type: 文件MIME类型
            
        Returns:
            dict: {"success": bool, "object_key": str, "url": str, "error": str}
        """
        import asyncio
        
        try:
            # 在线程池中执行同步的OSS上传操作
            result = await asyncio.to_thread(
                self.bucket.put_object,
                object_key,
                file_stream,
                headers={"Content-Type": content_type}
            )
            
            url = self.get_object_url(object_key)
            
            return {
                "success": True,
                "object_key": object_key,
                "url": url,
                "etag": result.etag,
                "error": None
            }
        except Exception as e:
            logger.error(f"Failed to upload stream to OSS: {str(e)}")
            return {
                "success": False,
                "object_key": object_key,
                "url": None,
                "error": str(e)
            }
    
    def get_object_url(self, object_key: str, expires: int = 3600) -> str:
        """
        获取对象的访问URL（带签名）
        
        Args:
            object_key: OSS对象Key
            expires: URL有效期（秒），默认1小时
            
        Returns:
            str: 签名URL
        """
        try:
            url = self.bucket.sign_url('GET', object_key, expires)
            return url
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {str(e)}")
            return ""
    
    def get_public_url(self, object_key: str) -> str:
        """
        获取对象的公开访问URL（不带签名，需要Bucket设置为公共读）
        
        Args:
            object_key: OSS对象Key
            
        Returns:
            str: 公开URL
        """
        # 格式：https://{bucket}.{endpoint}/{object_key}
        return f"https://{self.bucket_name}.{self.endpoint}/{object_key}"
    
    async def delete_object(self, object_key: str) -> bool:
        """
        删除OSS对象
        
        Args:
            object_key: OSS对象Key
            
        Returns:
            bool: 是否删除成功
        """
        try:
            self.bucket.delete_object(object_key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete object from OSS: {str(e)}")
            return False
    
    async def object_exists(self, object_key: str) -> bool:
        """
        检查对象是否存在
        
        Args:
            object_key: OSS对象Key
            
        Returns:
            bool: 是否存在
        """
        try:
            return self.bucket.object_exists(object_key)
        except Exception as e:
            logger.error(f"Failed to check object existence: {str(e)}")
            return False
    
    async def get_object_meta(self, object_key: str) -> Optional[Dict[str, Any]]:
        """
        获取对象元数据
        
        Args:
            object_key: OSS对象Key
            
        Returns:
            dict: 对象元数据，包括大小、类型等
        """
        try:
            meta = self.bucket.get_object_meta(object_key)
            return {
                "content_length": int(meta.headers.get("Content-Length", 0)),
                "content_type": meta.headers.get("Content-Type", ""),
                "etag": meta.headers.get("ETag", ""),
                "last_modified": meta.headers.get("Last-Modified", "")
            }
        except Exception as e:
            logger.error(f"Failed to get object meta: {str(e)}")
            return None
    
    def generate_presigned_upload_url(
        self,
        object_key: str,
        expires: int = 3600,
        content_type: str = "video/mp4"
    ) -> str:
        """
        生成预签名上传URL（用于前端直传）
        
        Args:
            object_key: OSS对象Key
            expires: URL有效期（秒）
            content_type: 文件MIME类型
            
        Returns:
            str: 预签名上传URL
        """
        try:
            url = self.bucket.sign_url(
                'PUT',
                object_key,
                expires,
                headers={'Content-Type': content_type}
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned upload URL: {str(e)}")
            return ""
    
    async def get_object_range(
        self,
        object_key: str,
        start: int = 0,
        end: Optional[int] = None
    ) -> Any:
        """
        获取对象的部分内容（通过Range请求）
        
        Args:
            object_key: OSS对象Key
            start: 起始字节（包含）
            end: 结束字节（包含），如果为None则读取到末尾
            
        Returns:
            file-like object or bytes
        """
        import asyncio
        
        # 定义Range头
        byte_range = None
        if end is not None:
            byte_range = (start, end)
        else:
            byte_range = (start, None)
            
        try:
            # 在线程池中执行同步的OSS下载操作
            # 注意: get_object 返回的是一个流式响应对象
            result = await asyncio.to_thread(
                self.bucket.get_object,
                object_key,
                byte_range=byte_range
            )
            return result
        except Exception as e:
            logger.error(f"Failed to get object range: {str(e)}")
            return None
    
    async def download_file(self, object_key: str, local_path: str) -> bool:
        """
        下载文件到本地（使用流式下载）
        """
        import asyncio
        import shutil
        
        try:
            # 获取流对象
            # stream = self.bucket.get_object(object_key)
            # oss2.Bucket.get_object returns a file-like object with read()
            
            def _download():
                result = self.bucket.get_object(object_key)
                with open(local_path, 'wb') as f:
                    shutil.copyfileobj(result, f, length=1024*1024) # 1MB chunks
                return True

            await asyncio.to_thread(_download)
            return True
        except Exception as e:
            logger.error(f"Failed to download file {object_key}: {str(e)}")
            return False


# 创建全局实例
oss_provider = OSSProvider()
