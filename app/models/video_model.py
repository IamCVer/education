"""
视频相关的数据库模型定义

本模块定义了视频教学功能的所有数据表模型：
- Video: 视频元数据
- Course: 课程信息
- CourseVideo: 课程与视频的关联关系
- VideoWatchProgress: 用户观看进度
"""

from tortoise import fields
from tortoise.models import Model


class Course(Model):
    """
    课程模型
    
    用于组织和管理教学视频，一个课程可以包含多个视频
    """
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, description="课程名称")
    description = fields.TextField(null=True, description="课程描述")
    teacher_id = fields.IntField(description="教师用户ID")
    cover_image = fields.CharField(max_length=500, null=True, description="课程封面图片URL")
    is_published = fields.BooleanField(default=False, description="是否已发布")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "courses"
        indexes = [("teacher_id",)]


class Video(Model):
    """
    视频模型
    
    存储视频的元数据信息，实际视频文件存储在MediaCMS和阿里云OSS中
    """
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255, description="视频标题")
    description = fields.TextField(null=True, description="视频描述")
    teacher_id = fields.IntField(description="上传教师的用户ID")
    
    # MediaCMS相关字段
    mediacms_video_id = fields.CharField(max_length=100, unique=True, null=True, 
                                         description="MediaCMS中的视频唯一ID")
    mediacms_video_url = fields.CharField(max_length=500, null=True, 
                                          description="MediaCMS视频页面URL")
    
    # 阿里云OSS相关字段
    oss_object_key = fields.CharField(max_length=500, null=True, 
                                      description="阿里云OSS对象存储Key")
    oss_url = fields.CharField(max_length=500, null=True, 
                               description="阿里云OSS访问URL")
    
    # 视频属性
    duration = fields.IntField(null=True, description="视频时长（秒）")
    thumbnail_url = fields.CharField(max_length=500, null=True, description="缩略图URL")
    thumbnail_object_key = fields.CharField(max_length=255, null=True, description="缩略图OSS对象Key")
    file_size = fields.BigIntField(null=True, description="文件大小（字节）")
    
    # 状态管理
    status = fields.CharField(
        max_length=20,
        default="uploading",
        description="视频处理状态: uploading/processing/ready/failed"
    )
    
    # 可见性控制
    visibility = fields.CharField(
        max_length=20,
        default="course_only",
        description="可见性: public/private/course_only"
    )
    
    # 统计数据
    view_count = fields.IntField(default=0, description="观看次数")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "videos"
        indexes = [
            ("teacher_id",),
            ("status",),
            ("mediacms_video_id",),
        ]


class CourseVideo(Model):
    """
    课程-视频关联模型
    
    多对多关系：一个课程可以包含多个视频，一个视频可以属于多个课程
    """
    id = fields.IntField(pk=True)
    course_id = fields.IntField(description="课程ID")
    video_id = fields.IntField(description="视频ID")
    order = fields.IntField(default=0, description="视频在课程中的排序")
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "course_videos"
        unique_together = (("course_id", "video_id"),)
        indexes = [
            ("course_id",),
            ("video_id",),
        ]


class VideoWatchProgress(Model):
    """
    视频观看进度模型
    
    记录每个用户对每个视频的观看进度
    """
    id = fields.IntField(pk=True)
    video_id = fields.IntField(description="视频ID")
    user_id = fields.IntField(description="用户ID")
    progress_seconds = fields.IntField(default=0, description="观看进度（秒）")
    completed = fields.BooleanField(default=False, description="是否已看完")
    last_watched_at = fields.DatetimeField(null=True, description="最后观看时间")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "video_watch_progress"
        unique_together = (("user_id", "video_id"),)
        indexes = [
            ("user_id",),
            ("video_id",),
        ]
