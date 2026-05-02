"""
视频管理API端点

提供视频上传、查询、更新、删除等HTTP API
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Query, Request, BackgroundTasks

from app.api.deps import get_current_user, get_admin_user
from app.models.user_model import User, UserRole
from app.services import video_service
from app.data_access import video_db
from app.schemas.video_schemas import (
    VideoCreate, VideoUpdate, VideoResponse,
    VideoListResponse, VideoDetailResponse,
    WatchProgressUpdate, WatchProgressResponse,
    VideoProcessingStatus, VideoStatsDetailResponse
)

router = APIRouter()


@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(..., description="视频文件"),
    title: str = Form(..., description="视频标题"),
    description: Optional[str] = Form(None, description="视频描述"),
    visibility: str = Form("course_only", description="可见性：public/private/course_only"),
    course_id: Optional[int] = Form(None, description="所属课程ID（可选）"),
    current_user: User = Depends(get_current_user)
):
    """
    上传视频（仅教师和管理员）
    
    上传流程：
    1. 文件上传到阿里云OSS
    2. 文件提交到MediaCMS进行转码
    3. 返回视频ID
    4. 如果指定了课程，将视频添加到课程
    """
    # 权限检查：只有教师和管理员可以上传
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can upload videos"
        )
    
    # 文件类型检查
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only video files are allowed"
        )
    
    result = await video_service.upload_video(
        file=file,
        title=title,
        teacher_id=current_user.id,
        description=description,
        visibility=visibility
    )
    
    # 如果指定了课程，将视频添加到课程
    if course_id and result.get("video_id"):
        try:
            await video_db.add_video_to_course(course_id, result["video_id"])
        except Exception as e:
            # 视频已上传成功，课程关联失败不影响返回结果
            print(f"Failed to add video to course: {str(e)}")
    
    return result


@router.get("", response_model=VideoListResponse)
async def list_videos(
    skip: int = 0,
    limit: int = 20,
    teacher_id: Optional[int] = None,
    visibility: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    获取视频列表（分页）
    
    - 学生只能看到公开和course_only的视频
    - 教师可以看到自己的所有视频
    - 管理员可以看到所有视频
    """
    # 权限过滤
    if current_user.role == UserRole.STUDENT:
        # 学生只能看到公开和course_only的视频
        if visibility not in ["public", "course_only", None]:
            visibility = "public"
        # 学生需要获取观看进度
        return await video_service.list_videos(skip, limit, teacher_id, visibility, None, current_user.id)
    elif current_user.role == UserRole.TEACHER and teacher_id is None:
        # 教师默认只看自己的视频
        teacher_id = current_user.id
    
    return await video_service.list_videos(skip, limit, teacher_id, visibility)


@router.get("/my", response_model=VideoListResponse)
async def get_my_videos(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """
    获取当前用户的视频列表（教师端）
    
    - 教师获取自己上传的所有视频
    - 学生获取自己有权访问的视频
    """
    # 计算skip和limit
    skip = (page - 1) * page_size
    limit = page_size
    
    # 教师获取自己的视频
    if current_user.role in [UserRole.TEACHER, UserRole.ADMIN]:
        teacher_id = current_user.id
        visibility = None  # 获取所有可见性的视频
    else:
        # 学生获取可访问的视频
        teacher_id = None
        visibility = "public"
    
    return await video_service.list_videos(skip, limit, teacher_id, visibility, background_tasks)


@router.get("/{video_id}", response_model=VideoDetailResponse)
async def get_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """获取视频详情"""
    video = await video_service.get_video(video_id, current_user.id, background_tasks)
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # 权限检查
    if video["visibility"] == "private" and video["teacher_id"] != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this video"
            )
    
    return video


@router.put("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: int,
    update_data: VideoUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新视频信息（仅视频所有者或管理员）"""
    video = await video_db.get_video_by_id(video_id)
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # 权限检查
    if video.teacher_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this video"
        )
    
    updated_video = await video_service.update_video_info(video_id, update_data)
    
    if not updated_video:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update video"
        )
    
    return updated_video


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_user)
):
    """删除视频（仅视频所有者或管理员）"""
    video = await video_db.get_video_by_id(video_id)
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # 权限检查
    if video.teacher_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this video"
        )
    
    success = await video_service.delete_video_completely(video_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete video"
        )


@router.get("/{video_id}/status", response_model=VideoProcessingStatus)
async def get_video_status(
    video_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取视频处理状态"""
    status_info = await video_service.sync_video_status(video_id)
    
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    return status_info


@router.post("/{video_id}/watch", response_model=dict)
async def record_watch_progress(
    video_id: int,
    progress_data: WatchProgressUpdate,
    current_user: User = Depends(get_current_user)
):
    """记录观看进度"""
    success = await video_service.record_video_view(
        video_id,
        current_user.id,
        progress_data.progress_seconds
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    return {"message": "Progress recorded successfully"}


@router.get("/{video_id}/progress", response_model=WatchProgressResponse)
async def get_watch_progress(
    video_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取观看进度"""
    progress = await video_db.get_user_watch_progress(current_user.id, video_id)
    
    # 如果没有进度记录，返回默认值而不是404
    if not progress:
        from datetime import datetime
        now = datetime.now()
        return WatchProgressResponse(
            id=0,  # 临时ID，表示没有实际记录
            user_id=current_user.id,
            video_id=video_id,
            progress_seconds=0,
            completed=False,
            last_watched_at=None,
            created_at=now,
            updated_at=now
        )
    
    return WatchProgressResponse.model_validate(progress)


@router.post("/{video_id}/progress", response_model=dict)
async def update_video_progress(
    video_id: int,
    progress_data: dict,
    current_user: User = Depends(get_current_user)
):
    """
    更新视频观看进度
    
    progress_data应包含：
    - progress_seconds: 当前观看到的秒数
    """
    progress_seconds = progress_data.get("progress_seconds", 0)
    
    # 获取视频信息以获取总时长
    video = await video_db.get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # update_user_watch_progress 内部会在首次观看时自动增加观看次数
    # 保存进度到数据库
    await video_db.update_user_watch_progress(
        user_id=current_user.id,
        video_id=video_id,
        progress_seconds=progress_seconds,
        video_duration=video.duration
    )
    
    return {
        "video_id": video_id,
        "user_id": current_user.id,
        "progress_seconds": progress_seconds,
        "message": "进度已保存"
    }



@router.get("/{video_id}/stats", response_model=VideoStatsDetailResponse)
async def get_video_stats_detail(
    video_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取视频详细统计信息（仅教师和管理员）"""
    # 权限检查
    if current_user.role == UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can view video statistics"
        )
    
    stats = await video_service.get_video_stats(video_id)
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
        
    return stats


@router.get("/{video_id}/stream")
async def stream_video(
    video_id: int,
    request: Request,
    token: Optional[str] = Query(None, description="Auth token for video player")
):
    """
    流式传输视频（缓存+文件服务）
    1. 检查本地缓存是否存在
    2. 不存在则从OSS下载（完整下载）
    3. 使用FileResponse直接服务（自动处理Range）
    """
    from fastapi.responses import FileResponse
    from app.providers.oss_provider import oss_provider
    from app.core.security import verify_token
    import os
    import logging
    
    logger = logging.getLogger(__name__)

    # 1. 简化的权限验证 (只依赖Token payload，不查库以加快速度，或者查库确认是否存在)
    user_id = None
    if token:
         payload = verify_token(token)
         if payload:
             user_id = payload.get("sub")
    
    # 2. 获取视频信息
    video = await video_db.get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # 权限检查
    if video.visibility == "private":
         if not user_id or int(user_id) != video.teacher_id:
              raise HTTPException(status_code=403, detail="Private video")

    if not video.oss_object_key:
         raise HTTPException(status_code=404, detail="Video source not found")
         
    # 3. 缓存处理
    # 确保缓存目录存在
    cache_dir = "/code/media/cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
        
    # 定义本地文件名 (使用video_id防止文件名冲突)
    # 假设都是mp4，或者从oss key推断后缀
    local_filename = f"{video_id}.mp4"
    local_path = os.path.join(cache_dir, local_filename)
    
    # 如果文件不存在，或者大小为0 (下载失败留下的)，则下载
    if not os.path.exists(local_path) or os.path.getsize(local_path) == 0:
        logger.info(f"Caching video {video_id} from OSS...")
        success = await oss_provider.download_file(video.oss_object_key, local_path)
        if not success:
            raise HTTPException(status_code=502, detail="Failed to download video from OSS")
        logger.info(f"Video {video_id} cached successfully.")
        
    # 4. 返回文件响应 (自动处理Range)
    response = FileResponse(
        local_path,
        media_type="video/mp4",
        filename=video.title or "video.mp4"
    )
    
    # 添加必要的headers以支持视频流播放
    response.headers["Accept-Ranges"] = "bytes"
    response.headers["Cache-Control"] = "no-cache"
    
    return response
