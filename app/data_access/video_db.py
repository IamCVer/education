"""
视频相关的数据访问层

本模块封装所有与视频、课程相关的数据库操作
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models.video_model import Video, Course, CourseVideo, VideoWatchProgress

logger = logging.getLogger(__name__)


# ============ 课程数据访问 ============

async def create_course(
    name: str,
    teacher_id: int,
    description: Optional[str] = None,
    cover_image: Optional[str] = None,
    is_published: bool = False
) -> Course:
    """
    创建新课程
    
    Args:
        name: 课程名称
        teacher_id: 教师用户ID
        description: 课程描述
        cover_image: 封面图片URL
        is_published: 是否发布
        
    Returns:
        Course: 创建的课程对象
    """
    course = await Course.create(
        name=name,
        teacher_id=teacher_id,
        description=description,
        cover_image=cover_image,
        is_published=is_published
    )
    return course


async def get_course_by_id(course_id: int) -> Optional[Course]:
    """根据ID获取课程"""
    return await Course.get_or_none(id=course_id)


async def get_courses_by_teacher(teacher_id: int, skip: int = 0, limit: int = 100) -> List[Course]:
    """获取教师的所有课程"""
    return await Course.filter(teacher_id=teacher_id).offset(skip).limit(limit).all()


async def get_all_courses(skip: int = 0, limit: int = 100, published_only: bool = False) -> List[Course]:
    """获取所有课程（支持分页）"""
    query = Course.all()
    if published_only:
        query = query.filter(is_published=True)
    return await query.offset(skip).limit(limit).all()


async def update_course(course_id: int, **update_data) -> Optional[Course]:
    """更新课程信息"""
    course = await Course.get_or_none(id=course_id)
    if not course:
        return None
    
    await course.update_from_dict(update_data)
    await course.save()
    return course


async def delete_course(course_id: int) -> bool:
    """删除课程"""
    course = await Course.get_or_none(id=course_id)
    if not course:
        return False
    await course.delete()
    return True


async def count_courses(teacher_id: Optional[int] = None, published_only: bool = False) -> int:
    """统计课程数量"""
    query = Course.all()
    if teacher_id:
        query = query.filter(teacher_id=teacher_id)
    if published_only:
        query = query.filter(is_published=True)
    return await query.count()


# ============ 视频数据访问 ============

async def create_video(
    title: str,
    teacher_id: int,
    description: Optional[str] = None,
    visibility: str = "course_only",
    mediacms_video_id: Optional[str] = None,
    oss_object_key: Optional[str] = None
) -> Video:
    """
    创建新视频记录
    
    Args:
        title: 视频标题
        teacher_id: 教师用户ID
        description: 视频描述
        visibility: 可见性
        mediacms_video_id: MediaCMS视频ID
        oss_object_key: OSS对象Key
        
    Returns:
        Video: 创建的视频对象
    """
    video = await Video.create(
        title=title,
        teacher_id=teacher_id,
        description=description,
        visibility=visibility,
        mediacms_video_id=mediacms_video_id,
        oss_object_key=oss_object_key,
        status="uploading"
    )
    return video


async def get_video_by_id(video_id: int) -> Optional[Video]:
    """根据ID获取视频"""
    return await Video.get_or_none(id=video_id)


async def get_video_by_mediacms_id(mediacms_video_id: str) -> Optional[Video]:
    """根据MediaCMS ID获取视频"""
    return await Video.get_or_none(mediacms_video_id=mediacms_video_id)


async def get_videos_by_teacher(teacher_id: int, skip: int = 0, limit: int = 100) -> List[Video]:
    """获取教师的所有视频"""
    return await Video.filter(teacher_id=teacher_id).offset(skip).limit(limit).order_by("-created_at").all()


async def get_videos_by_status(status: str, skip: int = 0, limit: int = 100) -> List[Video]:
    """根据状态获取视频"""
    return await Video.filter(status=status).offset(skip).limit(limit).all()


async def get_all_videos(skip: int = 0, limit: int = 100, visibility: Optional[str] = None) -> List[Video]:
    """获取所有视频（支持分页和可见性筛选）"""
    query = Video.all()
    if visibility:
        query = query.filter(visibility=visibility)
    return await query.offset(skip).limit(limit).order_by("-created_at").all()


async def update_video(video_id: int, **update_data) -> Optional[Video]:
    """更新视频信息"""
    video = await Video.get_or_none(id=video_id)
    if not video:
        return None
    
    await video.update_from_dict(update_data)
    await video.save()
    return video


async def update_video_status(video_id: int, status: str, **extra_data) -> Optional[Video]:
    """更新视频状态"""
    update_data = {"status": status, **extra_data}
    return await update_video(video_id, **update_data)


async def increment_view_count(video_id: int) -> bool:
    """增加视频观看次数"""
    video = await Video.get_or_none(id=video_id)
    if not video:
        return False
    video.view_count += 1
    await video.save()
    return True


async def delete_video(video_id: int) -> bool:
    """删除视频"""
    video = await Video.get_or_none(id=video_id)
    if not video:
        return False
    await video.delete()
    return True


async def count_videos(teacher_id: Optional[int] = None, status: Optional[str] = None) -> int:
    """统计视频数量"""
    query = Video.all()
    if teacher_id:
        query = query.filter(teacher_id=teacher_id)
    if status:
        query = query.filter(status=status)
    return await query.count()


# ============ 课程-视频关联数据访问 ============

async def add_video_to_course(course_id: int, video_id: int, order: int = 0) -> CourseVideo:
    """将视频添加到课程"""
    course_video = await CourseVideo.create(
        course_id=course_id,
        video_id=video_id,
        order=order
    )
    return course_video


async def remove_video_from_course(course_id: int, video_id: int) -> bool:
    """从课程中移除视频"""
    course_video = await CourseVideo.get_or_none(course_id=course_id, video_id=video_id)
    if not course_video:
        return False
    await course_video.delete()
    return True


async def get_course_videos(course_id: int) -> List[int]:
    """获取课程的所有视频ID（按顺序）"""
    course_videos = await CourseVideo.filter(course_id=course_id).order_by("order").all()
    return [cv.video_id for cv in course_videos]


async def get_video_courses(video_id: int) -> List[int]:
    """获取视频所属的所有课程ID"""
    course_videos = await CourseVideo.filter(video_id=video_id).all()
    return [cv.course_id for cv in course_videos]


async def update_video_order_in_course(course_id: int, video_id: int, new_order: int) -> bool:
    """更新视频在课程中的排序"""
    course_video = await CourseVideo.get_or_none(course_id=course_id, video_id=video_id)
    if not course_video:
        return False
    course_video.order = new_order
    await course_video.save()
    return True


async def reorder_course_videos(course_id: int, video_orders: List[Dict[str, int]]) -> bool:
    """
    批量重新排序课程视频
    
    Args:
        course_id: 课程ID
        video_orders: 视频ID和排序的列表，格式：[{"video_id": 1, "order": 0}, ...]
        
    Returns:
        bool: 是否成功
    """
    for item in video_orders:
        video_id = item.get("video_id")
        order = item.get("order", 0)
        await update_video_order_in_course(course_id, video_id, order)
    return True


# ============ 观看进度数据访问 ============

async def get_or_create_watch_progress(user_id: int, video_id: int) -> VideoWatchProgress:
    """获取或创建观看进度记录"""
    progress = await VideoWatchProgress.get_or_none(user_id=user_id, video_id=video_id)
    if not progress:
        progress = await VideoWatchProgress.create(
            user_id=user_id,
            video_id=video_id,
            progress_seconds=0,
            completed=False
        )
    return progress


async def update_watch_progress(
    user_id: int,
    video_id: int,
    progress_seconds: int,
    completed: bool = False
) -> VideoWatchProgress:
    """
    更新观看进度
    
    Args:
        user_id: 用户ID
        video_id: 视频ID
        progress_seconds: 观看进度（秒）
        completed: 是否已看完
        
    Returns:
        VideoWatchProgress: 更新后的进度对象
    """
    progress = await get_or_create_watch_progress(user_id, video_id)
    progress.progress_seconds = progress_seconds
    progress.completed = completed
    progress.last_watched_at = datetime.utcnow()
    await progress.save()
    return progress


async def get_user_all_progress(user_id: int, skip: int = 0, limit: int = 100) -> List[VideoWatchProgress]:
    """获取用户的所有观看进度"""
    return await VideoWatchProgress.filter(user_id=user_id).offset(skip).limit(limit).all()


async def get_video_completion_stats(video_id: int) -> Dict[str, Any]:
    """
    获取视频的完成统计
    
    Returns:
        dict: {"total_viewers": int, "completed_viewers": int, "completion_rate": float}
    """
    total = await VideoWatchProgress.filter(video_id=video_id).count()
    completed = await VideoWatchProgress.filter(video_id=video_id, completed=True).count()
    
    return {
        "total_viewers": total,
        "completed_viewers": completed,
        "completion_rate": (completed / total * 100) if total > 0 else 0.0
    }


async def get_video_watch_details(video_id: int) -> List[Dict[str, Any]]:
    """
    获取视频的详细观看记录（包含用户信息）
    """
    from app.models.user_model import User
    
    # 获取该视频的所有观看记录
    progress_records = await VideoWatchProgress.filter(video_id=video_id).all()
    
    results = []
    for progress in progress_records:
        user = await User.get_or_none(id=progress.user_id)
        if user:
            results.append({
                "user_id": user.id,
                "username": user.email, # 使用email作为username
                "progress_seconds": progress.progress_seconds,
                "completed": progress.completed,
                "last_watched_at": progress.last_watched_at
            })
            
    return results


async def get_course_completion_stats(course_id: int, user_id: int) -> Dict[str, Any]:
    """
    获取用户对某个课程的完成统计
    
    Returns:
        dict: {"total_videos": int, "completed_videos": int, "completion_rate": float}
    """
    video_ids = await get_course_videos(course_id)
    total = len(video_ids)
    
    if total == 0:
        return {"total_videos": 0, "completed_videos": 0, "completion_rate": 0.0}
    
    completed = await VideoWatchProgress.filter(
        user_id=user_id,
        video_id__in=video_ids,
        completed=True
    ).count()
    
    return {
        "total_videos": total,
        "completed_videos": completed,
        "completion_rate": (completed / total * 100) if total > 0 else 0.0
    }


async def get_user_watch_progress(user_id: int, video_id: int) -> Optional[VideoWatchProgress]:
    """
    获取用户对某个视频的观看进度
    
    Args:
        user_id: 用户ID
        video_id: 视频ID
        
    Returns:
        VideoWatchProgress: 观看进度记录，如果不存在则返回None
    """
    return await VideoWatchProgress.get_or_none(user_id=user_id, video_id=video_id)


async def update_user_watch_progress(
    user_id: int,
    video_id: int,
    progress_seconds: int,
    video_duration: Optional[int] = None
) -> VideoWatchProgress:
    """
    更新或创建用户的视频观看进度。
    若为首次观看（新建记录），同时自动增加视频观看次数。
    
    Args:
        user_id: 用户ID
        video_id: 视频ID
        progress_seconds: 当前观看到的秒数
        video_duration: 视频总时长（用于计算是否完成）
        
    Returns:
        VideoWatchProgress: 更新后的进度记录
    """
    # 获取或创建进度记录
    progress, created = await VideoWatchProgress.get_or_create(
        user_id=user_id,
        video_id=video_id,
        defaults={"progress_seconds": 0, "completed": False}
    )
    
    # 首次观看时（新建记录）增加观看次数
    if created:
        video = await Video.get_or_none(id=video_id)
        if video:
            video.view_count = (video.view_count or 0) + 1
            await video.save()
            logger.info(f"👁 Video {video_id} view_count incremented to {video.view_count} for new viewer user {user_id}")
    
    # 更新进度
    progress.progress_seconds = progress_seconds
    progress.last_watched_at = datetime.now()
    
    # 判断是否完成（观看进度达到95%以上视为完成）
    if video_duration and video_duration > 0:
        if progress_seconds >= video_duration * 0.95:
            progress.completed = True
            logger.info(f"✅ Video {video_id} marked as COMPLETED for user {user_id} (progress: {progress_seconds}/{video_duration}s, {round(progress_seconds/video_duration*100, 1)}%)")
        else:
            progress.completed = False
            percentage = round((progress_seconds / video_duration) * 100, 1)
            logger.info(f"📊 Video {video_id} progress updated for user {user_id}: {progress_seconds}s / {video_duration}s ({percentage}%)")
    else:
        logger.info(f"📊 Video {video_id} progress updated for user {user_id}: {progress_seconds}s (no duration info)")
    
    await progress.save()
    return progress
