"""
视频服务业务逻辑层

编排视频上传、处理、管理的完整业务流程
"""

import os
import tempfile
from typing import Optional, List, Dict, Any
import logging

from fastapi import UploadFile

from app.data_access import video_db
from app.providers.mediacms_provider import mediacms_provider
from app.providers.oss_provider import oss_provider
from app.schemas.video_schemas import (
    VideoCreate, VideoUpdate, VideoResponse,
    VideoListResponse, VideoProcessingStatus
)

logger = logging.getLogger(__name__)

# 全局正在处理的缩略图提取任务集合，防止重复触发
_processing_tasks = set()


async def upload_video(
    file: UploadFile,
    title: str,
    teacher_id: int,
    description: Optional[str] = None,
    visibility: str = "course_only"
) -> Dict[str, Any]:
    """
    上传视频的完整流程
    
    流程：
    1. 创建视频记录（状态：uploading）
    2. 上传文件到阿里云OSS
    3. 上传文件到MediaCMS进行转码
    4. 更新视频记录（添加OSS和MediaCMS信息）
    
    Args:
        file: 上传的视频文件
        title: 视频标题
        teacher_id: 教师ID
        description: 视频描述
        visibility: 可见性
        
    Returns:
        dict: {"video_id": int, "message": str}
    """
    temp_file_path = None
    
    try:
        # 1. 创建视频记录
        video = await video_db.create_video(
            title=title,
            teacher_id=teacher_id,
            description=description,
            visibility=visibility
        )
        
        # 2. 保存上传的文件到临时位置
        temp_file_path = os.path.join(tempfile.gettempdir(), f"video_{video.id}_{file.filename}")
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 3. 上传到阿里云OSS
        object_key = oss_provider.generate_object_key(teacher_id, file.filename)
        oss_result = await oss_provider.upload_file(
            temp_file_path,
            object_key,
            content_type=file.content_type or "video/mp4"
        )
        
        if not oss_result["success"]:
            await video_db.update_video_status(video.id, "failed")
            return {
                "success": False,
                "video_id": video.id,
                "message": f"OSS上传失败: {oss_result['error']}"
            }
        
        # 4. 上传到MediaCMS
        try:
            mediacms_result = await mediacms_provider.upload_video(
                temp_file_path,
                title,
                description,
                is_public=(visibility == "public")
            )
            
            mediacms_video_id = mediacms_result.get("id") or mediacms_result.get("friendly_token")
            mediacms_video_url = mediacms_result.get("url")
            
            # 5. 更新视频记录
            await video_db.update_video(
                video.id,
                mediacms_video_id=mediacms_video_id,
                mediacms_video_url=mediacms_video_url,
                oss_object_key=object_key,
                oss_url=oss_result["url"],
                status="processing"
            )
            
            return {
                "success": True,
                "video_id": video.id,
                "message": "视频上传成功，正在处理中"
            }
            
        except Exception as e:
            logger.error(f"MediaCMS upload failed: {str(e)}")
            # MediaCMS上传失败，但OSS已成功，视频仍然可用
            await video_db.update_video(
                video.id,
                oss_object_key=object_key,
                oss_url=oss_result["url"],
                status="ready"  # OSS上传成功，视频可以播放
            )
            return {
                "success": True,
                "video_id": video.id,
                "message": "视频上传成功（MediaCMS转码跳过）"
            }
    
    finally:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp file: {str(e)}")


async def extract_thumbnail(video_id: int) -> Optional[str]:
    """
    从视频中提取缩略图和时长（使用 FFmpeg/FFprobe）
    """
    import subprocess
    import os
    import json
    
    if video_id in _processing_tasks:
        logger.info(f"Thumbnail extraction for video {video_id} is already in progress")
        return None
        
    _processing_tasks.add(video_id)
    print(f"DEBUG: Starting extract_thumbnail for {video_id}", flush=True)
    
    try:
        video = await video_db.get_video_by_id(video_id)
        if not video or not video.oss_object_key:
            print(f"DEBUG: Video {video_id} not found or no key", flush=True)
            return None
            
        # 下载视频到临时文件
        from app.providers.oss_provider import oss_provider
        local_path = f"/tmp/v_{video_id}.mp4"
        thumb_path = f"/tmp/t_{video_id}.jpg"
        
        # 1. 确保本地有文件
        if not os.path.exists(local_path):
            print(f"DEBUG: Downloading video {video_id} to {local_path}", flush=True)
            success = await oss_provider.download_file(video.oss_object_key, local_path)
            if not success:
                print(f"DEBUG: Download failed for {video_id}", flush=True)
                return None
        
        print(f"DEBUG: File exists for {video_id}, size: {os.path.getsize(local_path)}", flush=True)
            
        # 2. 从视频中提取时长 (FFprobe)
        duration = 0
        try:
            print(f"DEBUG: Probing duration for {video_id}", flush=True)
            probe_cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json", 
                "-show_format", "-show_streams", local_path
            ]
            result = subprocess.run(probe_cmd, check=True, capture_output=True, text=True)
            probe_data = json.loads(result.stdout)
            duration = int(float(probe_data.get('format', {}).get('duration', 0)))
            print(f"DEBUG: Extracted duration {duration} for {video_id}", flush=True)
        except Exception as e:
            print(f"DEBUG: Probe failed for {video_id}: {e}", flush=True)

        # 3. 提取第 1 秒的帧 (FFmpeg)
        print(f"DEBUG: Running FFmpeg for {video_id}", flush=True)
        cmd = [
            "ffmpeg", "-y", "-i", local_path, 
            "-ss", "00:00:01", "-vframes", "1", 
            "-q:v", "2", thumb_path
        ]
        result = subprocess.run(cmd, capture_output=True)
        
        if os.path.exists(thumb_path):
            print(f"DEBUG: Thumbnail generated for {video_id}, uploading...", flush=True)
            # 将缩略图上传回 OSS
            new_thumb_key = f"thumbnails/v_{video_id}.jpg"
            upload_result = await oss_provider.upload_file(thumb_path, new_thumb_key, content_type="image/jpeg")
            
            if upload_result.get("success"):
                print(f"DEBUG: Thumbnail uploaded for {video_id}", flush=True)
                # 更新数据库 - 保存对象键而不是签名URL
                update_data = {"thumbnail_object_key": new_thumb_key}
                if duration > 0:
                    update_data["duration"] = duration
                    
                await video_db.update_video(video_id, **update_data)
                print(f"DEBUG: DB updated for {video_id}", flush=True)
                return new_thumb_key
            else:
                print(f"DEBUG: Upload failed for {video_id}: {upload_result.get('error')}", flush=True)
        else:
            print(f"DEBUG: FFmpeg output file missing for {video_id}", flush=True)
            if result.returncode != 0:
                print(f"DEBUG: FFmpeg Error: {result.stderr.decode()}", flush=True)
            
    except Exception as e:
        print(f"DEBUG: Exception in extract_thumbnail for {video_id}: {str(e)}", flush=True)
    finally:
        # 从处理中集合移除
        if video_id in _processing_tasks:
            _processing_tasks.remove(video_id)
            
        # 清理临时文件
        if os.path.exists(local_path):
            try: os.remove(local_path)
            except: pass
        if os.path.exists(thumb_path):
            try: os.remove(thumb_path)
            except: pass
        
    return None


async def get_video(
    video_id: int, 
    user_id: Optional[int] = None,
    background_tasks: Optional[Any] = None
) -> Optional[Dict[str, Any]]:
    """
    获取视频详情
    
    Args:
        video_id: 视频ID
        user_id: 用户ID（可选，用于获取观看进度）
        background_tasks: FastAPI 背景任务对象（可选）
        
    Returns:
        dict: 视频详情，包括观看进度
    """
    video = await video_db.get_video_by_id(video_id)
    if not video:
        return None
    
    video_dict = {
        "id": video.id,
        "title": video.title,
        "description": video.description,
        "teacher_id": video.teacher_id,
        "mediacms_video_id": video.mediacms_video_id,
        "mediacms_video_url": video.mediacms_video_url,
        "oss_url": video.oss_url,
        "oss_object_key": video.oss_object_key,
        "duration": video.duration,
        "thumbnail_url": video.thumbnail_url,
        "file_size": video.file_size,
        "status": video.status,
        "visibility": video.visibility,
        "view_count": video.view_count,
        "created_at": video.created_at,
        "updated_at": video.updated_at
    }
    
    # 如果没有缩略图或时长，且视频已就绪，触发异步提取
    if (not video.thumbnail_url or not video.duration) and video.status == "ready":
        if video_id not in _processing_tasks:
            logger.info(f"Triggering background extraction for video {video_id}")
            if background_tasks:
                background_tasks.add_task(extract_thumbnail, video_id)
            else:
                import asyncio
                asyncio.create_task(extract_thumbnail(video_id))
    
    # 如果提供了用户ID，获取观看进度
    if user_id:
        progress = await video_db.get_user_watch_progress(user_id, video_id)
        if progress:
            video_dict["watch_progress"] = {
                "id": progress.id,
                "video_id": progress.video_id,
                "user_id": progress.user_id,
                "progress_seconds": progress.progress_seconds,
                "completed": progress.completed,
                "last_watched_at": progress.last_watched_at,
                "created_at": progress.created_at,
                "updated_at": progress.updated_at
            }
    
    # 生成代理播放URL
    from app.core.security import create_access_token
    from datetime import timedelta
    
    token_param = ""
    if user_id:
        access_token_expires = timedelta(hours=1)
        access_token = create_access_token(
            data={"sub": str(user_id)}, expires_delta=access_token_expires
        )
        token_param = f"?token={access_token}"
    
    proxy_url = f"/api/v1/videos/{video_id}/stream{token_param}"
    
    # 优先使用OSS签名URL作为视频播放地址（避免后端代理的性能瓶颈和超时问题）
    if video.oss_object_key:
        # 生成1小时有效期的签名URL
        signed_oss_url = oss_provider.get_object_url(video.oss_object_key, expires=3600)
        video_dict["video_url"] = signed_oss_url
        video_dict["oss_url"] = signed_oss_url # 保持兼容性
    else:
        # 只有在没有OSS Key的情况下才使用代理
        video_dict["video_url"] = proxy_url

    return video_dict


async def list_videos(
    skip: int = 0,
    limit: int = 20,
    teacher_id: Optional[int] = None,
    visibility: Optional[str] = None,
    background_tasks: Optional[Any] = None,
    user_id: Optional[int] = None
) -> VideoListResponse:
    """
    获取视频列表（分页）
    
    Args:
        skip: 跳过数量
        limit: 每页数量
        teacher_id: 筛选教师ID
        visibility: 筛选可见性
        background_tasks: FastAPI 背景任务对象（可选）
        user_id: 用户ID（用于获取观看进度）
        
    Returns:
        VideoListResponse: 分页视频列表
    """
    if teacher_id:
        videos = await video_db.get_videos_by_teacher(teacher_id, skip, limit)
        total = await video_db.count_videos(teacher_id=teacher_id)
    else:
        videos = await video_db.get_all_videos(skip, limit, visibility)
        total = await video_db.count_videos()
    
    # 异步检查并为需要的视频触发提取任务
    for v in videos:
        if (not v.thumbnail_url or not v.duration) and v.status == "ready":
            if v.id not in _processing_tasks:
                logger.info(f"Triggering background extraction for video {v.id} from list")
                if background_tasks:
                    background_tasks.add_task(extract_thumbnail, v.id)
                else:
                    import asyncio
                    asyncio.create_task(extract_thumbnail(v.id))
    
    # 构建响应，如果提供了user_id则包含观看进度
    video_responses = []
    
    for v in videos:
        video_dict = VideoResponse.model_validate(v).model_dump()
        
        # 如果有缩略图对象键，生成新的签名URL
        if v.thumbnail_object_key:
            try:
                video_dict["thumbnail_url"] = oss_provider.get_object_url(v.thumbnail_object_key, expires=3600)
            except Exception as e:
                logger.warning(f"Failed to generate thumbnail URL for video {v.id}: {e}")
                video_dict["thumbnail_url"] = None
        
        # 如果提供了user_id，添加观看进度
        if user_id:
            progress = await video_db.get_user_watch_progress(user_id, v.id)
            if progress:
                video_dict["watch_progress"] = {
                    "id": progress.id,
                    "video_id": progress.video_id,
                    "user_id": progress.user_id,
                    "progress_seconds": progress.progress_seconds,
                    "completed": progress.completed,
                    "last_watched_at": progress.last_watched_at,
                    "created_at": progress.created_at,
                    "updated_at": progress.updated_at
                }
                # Debug logging
                logger.info(f"Video {v.id} '{v.title}' - Progress: {progress.progress_seconds}s, Completed: {progress.completed}")

        
        video_responses.append(video_dict)
            
    return VideoListResponse(
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        videos=video_responses
    )


async def update_video_info(
    video_id: int,
    update_data: VideoUpdate
) -> Optional[VideoResponse]:
    """
    更新视频信息
    
    Args:
        video_id: 视频ID
        update_data: 更新数据
        
    Returns:
        VideoResponse: 更新后的视频信息
    """
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # 同步更新MediaCMS
    video = await video_db.get_video_by_id(video_id)
    if video and video.mediacms_video_id:
        await mediacms_provider.update_video(
            video.mediacms_video_id,
            title=update_dict.get("title"),
            description=update_dict.get("description"),
            is_public=(update_dict.get("visibility") == "public")
        )
    
    # 更新数据库
    updated_video = await video_db.update_video(video_id, **update_dict)
    if not updated_video:
        return None
    
    return VideoResponse.model_validate(updated_video)


async def delete_video_completely(video_id: int) -> bool:
    """
    完全删除视频（包括OSS和MediaCMS）
    
    Args:
        video_id: 视频ID
        
    Returns:
        bool: 是否删除成功
    """
    video = await video_db.get_video_by_id(video_id)
    if not video:
        return False
    
    # 1. 删除MediaCMS中的视频
    if video.mediacms_video_id:
        await mediacms_provider.delete_video(video.mediacms_video_id)
    
    # 2. 删除OSS中的文件
    if video.oss_object_key:
        await oss_provider.delete_object(video.oss_object_key)
    
    # 3. 删除数据库记录
    return await video_db.delete_video(video_id)


async def sync_video_status(video_id: int) -> Optional[VideoProcessingStatus]:
    """
    同步视频处理状态（从MediaCMS）
    
    Args:
        video_id: 视频ID
        
    Returns:
        VideoProcessingStatus: 处理状态
    """
    video = await video_db.get_video_by_id(video_id)
    if not video or not video.mediacms_video_id:
        return None
    
    # 从MediaCMS获取状态
    status_info = await mediacms_provider.check_processing_status(video.mediacms_video_id)
    
    # 更新数据库
    update_data = {"status": status_info["status"]}
    
    # 如果处理完成，获取额外信息
    if status_info["status"] == "ready":
        video_info = await mediacms_provider.get_video_info(video.mediacms_video_id)
        if video_info:
            update_data["duration"] = video_info.get("duration")
            update_data["thumbnail_url"] = video_info.get("thumbnail_url")
    
    await video_db.update_video(video_id, **update_data)
    
    return VideoProcessingStatus(
        video_id=video_id,
        status=status_info["status"],
        progress=status_info["progress"],
        message=status_info["message"]
    )


async def record_video_view(video_id: int, user_id: int, progress_seconds: int) -> bool:
    """
    记录视频观看进度
    
    Args:
        video_id: 视频ID
        user_id: 用户ID
        progress_seconds: 观看进度（秒）
        
    Returns:
        bool: 是否记录成功
    """
    video = await video_db.get_video_by_id(video_id)
    if not video:
        return False
    
    # update_user_watch_progress 内部会在首次观看时自动增加观看次数
    await video_db.update_user_watch_progress(user_id, video_id, progress_seconds, video.duration)
    
    return True


async def get_video_stats(video_id: int) -> Optional[Dict[str, Any]]:
    """
    获取视频的详细统计信息
    """
    video = await video_db.get_video_by_id(video_id)
    if not video:
        return None
        
    # 获取详细观看进度
    viewer_details = await video_db.get_video_watch_details(video_id)
    
    # 计算统计指标
    total_viewers = len(viewer_details)
    completed_viewers = sum(1 for v in viewer_details if v["completed"])
    
    total_progress_percent = 0
    if video.duration and video.duration > 0:
        for v in viewer_details:
            percent = min(100, int((v["progress_seconds"] / video.duration) * 100))
            v["progress_percent"] = percent
            total_progress_percent += percent
    else:
        for v in viewer_details:
            v["progress_percent"] = 0
            
    avg_progress = (total_progress_percent / total_viewers) if total_viewers > 0 else 0
    completion_rate = (completed_viewers / total_viewers * 100) if total_viewers > 0 else 0
    
    return {
        "video_id": video.id,
        "title": video.title,
        "total_view_count": video.view_count,
        "unique_viewers": total_viewers,
        "avg_progress_percent": round(avg_progress, 2),
        "completion_rate": round(completion_rate, 2),
        "viewers": viewer_details
    }
