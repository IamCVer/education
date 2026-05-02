# app/schemas/group_schemas.py
"""
[职责] 群组聊天相关的Pydantic模型
"""
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class CreateGroupRequest(BaseModel):
    """创建群聊请求"""
    group_name: str
    student_ids: List[int]


class GroupResponse(BaseModel):
    """群聊响应"""
    id: str
    name: str
    member_count: int
    created_at: str


class GroupListResponse(BaseModel):
    """群聊列表响应"""
    groups: List[GroupResponse]


class GroupMessageResponse(BaseModel):
    """群聊消息响应"""
    id: str
    sender_id: int
    sender_name: str
    sender_role: str  # teacher, student
    message: str
    message_type: str  # text, ai_response, system
    created_at: str


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    message: str


class InviteStudentsRequest(BaseModel):
    """邀请学生请求"""
    student_ids: List[int]


class AskAIRequest(BaseModel):
    """向AI提问请求"""
    question: str


# ========== 新增功能的Schema ==========

class UploadFileRequest(BaseModel):
    """上传文件请求"""
    file_name: str
    file_size: int


class SearchMessagesRequest(BaseModel):
    """搜索消息请求"""
    query: str
    limit: Optional[int] = 20


class PinMessageRequest(BaseModel):
    """置顶消息请求"""
    post_id: str


class SendMessageWithMentionsRequest(BaseModel):
    """发送带@提及的消息请求"""
    message: str
    mention_user_ids: Optional[List[int]] = []


class ReplyMessageRequest(BaseModel):
    """回复消息请求"""
    root_post_id: str
    message: str


class SetAnnouncementRequest(BaseModel):
    """设置群公告请求"""
    announcement: str


class MessageReactionRequest(BaseModel):
    """消息反应请求"""
    post_id: str
    emoji_name: str  # thumbsup, heart, smile, etc.


class FileInfo(BaseModel):
    """文件信息"""
    id: str
    name: str
    size: int
    mime_type: str
    url: str
    created_at: str


class ThreadInfo(BaseModel):
    """消息线程信息"""
    root_id: str
    reply_count: int
    participants: List[str]


class EnhancedMessageResponse(GroupMessageResponse):
    """增强的消息响应（包含新功能）"""
    file_ids: Optional[List[str]] = []
    files: Optional[List[FileInfo]] = []
    is_pinned: Optional[bool] = False
    mentions: Optional[List[int]] = []
    root_id: Optional[str] = None  # 如果是回复，指向父消息
    reply_count: Optional[int] = 0
    reactions: Optional[dict] = {}  # {emoji_name: [user_ids]}


# ========== 邀请审核功能的Schema ==========

class StudentInviteRequest(BaseModel):
    """学生邀请请求（需要理由和审核）"""
    invited_user_id: int
    reason: str  # 邀请理由


class TeacherInviteRequest(BaseModel):
    """老师邀请请求（直接加入）"""
    user_ids: List[int]


class GroupInvitationResponse(BaseModel):
    """邀请信息响应"""
    id: str
    group_id: str
    group_name: str
    inviter_id: int
    inviter_name: str
    inviter_role: str  # teacher, student
    invited_user_id: int
    invited_user_name: str
    reason: Optional[str] = None  # 学生邀请时的理由
    status: str  # pending, approved, rejected
    created_at: str
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[int] = None


class ReviewInvitationRequest(BaseModel):
    """审核邀请请求"""
    approved: bool
    reject_reason: Optional[str] = None  # 拒绝理由


class PendingInvitationsResponse(BaseModel):
    """待审核邀请列表响应"""
    invitations: List[GroupInvitationResponse]
    total_count: int
