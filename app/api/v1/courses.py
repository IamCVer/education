"""
课程管理API端点

提供课程创建、查询、更新、删除以及课程-视频关联管理
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from app.api.deps import get_current_user
from app.models.user_model import User, UserRole
from app.data_access import video_db
from app.services import video_service
from app.schemas.video_schemas import (
    CourseCreate, CourseUpdate, CourseResponse,
    CourseDetailResponse, AddVideoToCourseRequest,
    RemoveVideoFromCourseRequest, ReorderCourseVideosRequest
)

router = APIRouter()


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_current_user)
):
    """创建课程（仅教师和管理员）"""
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can create courses"
        )
    
    course = await video_db.create_course(
        name=course_data.name,
        teacher_id=current_user.id,
        description=course_data.description,
        cover_image=course_data.cover_image,
        is_published=course_data.is_published
    )
    
    course_dict = CourseResponse.model_validate(course).model_dump()
    course_dict["video_count"] = 0
    
    return course_dict


@router.get("", response_model=list[CourseResponse])
async def list_courses(
    skip: int = 0,
    limit: int = 20,
    teacher_id: Optional[int] = None,
    published_only: bool = False,
    current_user: User = Depends(get_current_user)
):
    """获取课程列表"""
    # 学生只能看到已发布的课程
    if current_user.role == UserRole.STUDENT:
        published_only = True
    
    if teacher_id:
        courses = await video_db.get_courses_by_teacher(teacher_id, skip, limit)
    else:
        courses = await video_db.get_all_courses(skip, limit, published_only)
    
    # 添加视频数量
    result = []
    for course in courses:
        course_dict = CourseResponse.model_validate(course).model_dump()
        video_ids = await video_db.get_course_videos(course.id)
        course_dict["video_count"] = len(video_ids)
        result.append(course_dict)
    
    return result


@router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """获取课程详情（包含视频列表）"""
    course = await video_db.get_course_by_id(course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # 权限检查：未发布的课程只有创建者和管理员可以查看
    if not course.is_published:
        if course.teacher_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this course"
            )
    
    # 获取课程视频
    video_ids = await video_db.get_course_videos(course_id)
    videos = []
    for vid in video_ids:
        video = await video_service.get_video(vid, current_user.id, background_tasks)
        if video:
            videos.append(video)
    
    course_dict = CourseResponse.model_validate(course).model_dump()
    course_dict["video_count"] = len(videos)
    course_dict["videos"] = videos
    
    return course_dict


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    update_data: CourseUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新课程信息（仅课程所有者或管理员）"""
    course = await video_db.get_course_by_id(course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # 权限检查
    if course.teacher_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this course"
        )
    
    update_dict = update_data.model_dump(exclude_unset=True)
    updated_course = await video_db.update_course(course_id, **update_dict)
    
    if not updated_course:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update course"
        )
    
    course_dict = CourseResponse.model_validate(updated_course).model_dump()
    video_ids = await video_db.get_course_videos(course_id)
    course_dict["video_count"] = len(video_ids)
    
    return course_dict


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user)
):
    """删除课程（仅课程所有者或管理员）"""
    course = await video_db.get_course_by_id(course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # 权限检查
    if course.teacher_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this course"
        )
    
    success = await video_db.delete_course(course_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete course"
        )


@router.post("/{course_id}/videos", response_model=dict)
async def add_video_to_course(
    course_id: int,
    request_data: AddVideoToCourseRequest,
    current_user: User = Depends(get_current_user)
):
    """添加视频到课程"""
    course = await video_db.get_course_by_id(course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # 权限检查
    if course.teacher_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this course"
        )
    
    # 检查视频是否存在
    video = await video_db.get_video_by_id(request_data.video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    try:
        await video_db.add_video_to_course(course_id, request_data.video_id, request_data.order)
        return {"message": "Video added to course successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add video to course: {str(e)}"
        )


@router.delete("/{course_id}/videos", response_model=dict)
async def remove_video_from_course(
    course_id: int,
    request_data: RemoveVideoFromCourseRequest,
    current_user: User = Depends(get_current_user)
):
    """从课程中移除视频"""
    course = await video_db.get_course_by_id(course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # 权限检查
    if course.teacher_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this course"
        )
    
    success = await video_db.remove_video_from_course(course_id, request_data.video_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found in this course"
        )
    
    return {"message": "Video removed from course successfully"}


@router.put("/{course_id}/videos/reorder", response_model=dict)
async def reorder_course_videos(
    course_id: int,
    request_data: ReorderCourseVideosRequest,
    current_user: User = Depends(get_current_user)
):
    """重新排序课程视频"""
    course = await video_db.get_course_by_id(course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # 权限检查
    if course.teacher_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this course"
        )
    
    await video_db.reorder_course_videos(course_id, request_data.video_orders)
    
    return {"message": "Videos reordered successfully"}
