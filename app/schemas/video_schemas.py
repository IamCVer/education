"""
视频相关的Pydantic Schema定义

本模块定义了视频教学功能的所有请求和响应模型
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============ 课程相关 Schema ============

class CourseCreate(BaseModel):
    """创建课程的请求模型"""
    name: str = Field(..., min_length=1, max_length=255, description="课程名称")
    description: Optional[str] = Field(None, description="课程描述")
    cover_image: Optional[str] = Field(None, max_length=500, description="课程封面图片URL")
    is_published: bool = Field(default=False, description="是否发布")


class CourseUpdate(BaseModel):
    """更新课程的请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    cover_image: Optional[str] = Field(None, max_length=500)
    is_published: Optional[bool] = None


class CourseResponse(BaseModel):
    """课程响应模型"""
    id: int
    name: str
    description: Optional[str]
    teacher_id: int
    cover_image: Optional[str]
    is_published: bool
    video_count: int = Field(default=0, description="课程包含的视频数量")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CourseDetailResponse(CourseResponse):
    """课程详情响应模型（包含视频列表）"""
    videos: List["VideoResponse"] = Field(default_factory=list, description="课程包含的视频列表")


# ============ 视频相关 Schema ============

class VideoCreate(BaseModel):
    """创建视频的请求模型"""
    title: str = Field(..., min_length=1, max_length=255, description="视频标题")
    description: Optional[str] = Field(None, description="视频描述")
    visibility: str = Field(default="course_only", description="可见性：public/private/course_only")


class VideoUpdate(BaseModel):
    """更新视频的请求模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    visibility: Optional[str] = None
    thumbnail_url: Optional[str] = Field(None, max_length=500)


class VideoResponse(BaseModel):
    """视频响应模型"""
    id: int
    title: str
    description: Optional[str]
    teacher_id: int
    mediacms_video_id: Optional[str]
    mediacms_video_url: Optional[str] = None
    oss_url: Optional[str] = None
    oss_object_key: Optional[str] = None
    video_url: Optional[str] = None  # 关键修复：设置为可选且默认为None
    duration: Optional[int] = None
    thumbnail_url: Optional[str]
    file_size: Optional[int]
    status: str
    visibility: str
    view_count: int
    created_at: datetime
    updated_at: datetime
    watch_progress: Optional["WatchProgressResponse"] = Field(None, description="当前用户的观看进度")
    
    # 移除 @property 和 model_dump，直接使用 Service 层返回的 video_url
    
    def dict(self, **kwargs):
        """Override dict for backward compatibility"""
        data = super().dict(**kwargs)
        data['video_url'] = self.video_url
        return data

    class Config:
        from_attributes = True


class VideoDetailResponse(VideoResponse):
    """视频详情响应模型（包含额外信息）"""
    courses: List[CourseResponse] = Field(default_factory=list, description="视频所属的课程列表")
    watch_progress: Optional["WatchProgressResponse"] = Field(None, description="当前用户的观看进度")


class VideoListResponse(BaseModel):
    """视频列表响应模型（分页）"""
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    videos: List[VideoResponse] = Field(..., description="视频列表")


# ============ 课程-视频关联 Schema ============

class AddVideoToCourseRequest(BaseModel):
    """添加视频到课程的请求模型"""
    video_id: int = Field(..., description="视频ID")
    order: int = Field(default=0, description="排序")


class RemoveVideoFromCourseRequest(BaseModel):
    """从课程移除视频的请求模型"""
    video_id: int = Field(..., description="视频ID")


class ReorderCourseVideosRequest(BaseModel):
    """重新排序课程视频的请求模型"""
    video_orders: List[dict] = Field(..., description="视频ID和排序的列表，格式：[{\"video_id\": 1, \"order\": 0}, ...]")


# ============ 观看进度相关 Schema ============

class WatchProgressUpdate(BaseModel):
    """更新观看进度的请求模型"""
    progress_seconds: int = Field(..., ge=0, description="观看进度（秒）")
    completed: bool = Field(default=False, description="是否已看完")


class WatchProgressResponse(BaseModel):
    """观看进度响应模型"""
    id: int
    video_id: int
    user_id: int
    progress_seconds: int
    completed: bool
    last_watched_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ 视频上传相关 Schema ============

class VideoUploadResponse(BaseModel):
    """视频上传响应模型"""
    video_id: int = Field(..., description="创建的视频ID")
    upload_url: Optional[str] = Field(None, description="OSS上传URL（如使用前端直传）")
    message: str = Field(default="视频上传成功", description="提示信息")


class VideoProcessingStatus(BaseModel):
    """视频处理状态响应模型"""
    video_id: int
    status: str = Field(..., description="processing状态：uploading/processing/ready/failed")
    progress: int = Field(default=0, ge=0, le=100, description="处理进度百分比")
    message: Optional[str] = Field(None, description="状态消息")


# ============ 统计相关 Schema ============

class VideoStatistics(BaseModel):
    """视频统计基础信息"""
    total_videos: int = Field(..., description="总视频数")
    total_view_count: int = Field(..., description="总观看次数")
    total_duration: int = Field(..., description="总时长（秒）")
    videos_by_status: dict = Field(..., description="各状态视频数量")


class VideoViewerStats(BaseModel):
    """单个用户的视频观看统计"""
    user_id: int
    username: str
    real_name: Optional[str] = None
    progress_seconds: int
    progress_percent: int
    completed: bool
    last_watched_at: Optional[datetime]


class VideoStatsDetailResponse(BaseModel):
    """视频详细统计响应模型"""
    video_id: int
    title: str
    total_view_count: int
    unique_viewers: int
    avg_progress_percent: float
    completion_rate: float
    viewers: List[VideoViewerStats]


class CourseStatistics(BaseModel):
    """课程统计信息"""
    total_courses: int = Field(..., description="总课程数")
    published_courses: int = Field(..., description="已发布课程数")
    total_students: int = Field(..., description="总学生数")
    completion_rate: float = Field(..., ge=0, le=100, description="平均完成率")


# 解决循环引用
CourseDetailResponse.model_rebuild()
VideoDetailResponse.model_rebuild()
VideoResponse.model_rebuild()
