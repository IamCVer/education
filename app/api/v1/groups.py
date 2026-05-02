# app/api/v1/groups.py
"""
[职责] 群组聊天API端点 - 作为前端和Mattermost之间的中间人
"""
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from app.api.deps import get_current_user
from app.models.user_model import User
from app.services.group_service import GroupService
from app.schemas.group_schemas import (
    CreateGroupRequest,
    GroupResponse,
    GroupListResponse,
    GroupMessageResponse,
    SendMessageRequest,
    AskAIRequest,
    InviteStudentsRequest,
    SearchMessagesRequest,
    PinMessageRequest,
    SendMessageWithMentionsRequest,
    ReplyMessageRequest,
    SetAnnouncementRequest,
    StudentInviteRequest,
    TeacherInviteRequest,
    GroupInvitationResponse,
    ReviewInvitationRequest,
    PendingInvitationsResponse
)

router = APIRouter()


@router.post("/groups/create", response_model=GroupResponse)
async def create_group(
    request: CreateGroupRequest,
    current_user: User = Depends(get_current_user)
):
    """
    创建群聊
    只有老师角色可以创建群聊
    """
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有老师可以创建群聊"
        )
    
    try:
        group_service = GroupService()
        group = await group_service.create_group(
            creator_id=current_user.id,
            group_name=request.group_name,
            student_ids=request.student_ids
        )
        return group
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"❌ 创建群聊失败: {error_msg}")
        print(f"详细错误:\n{traceback.format_exc()}")
        
        if "Mattermost" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="群聊服务暂时不可用，Mattermost 服务未正确配置"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建群聊失败: {error_msg}"
        )


@router.get("/groups", response_model=GroupListResponse)
async def get_user_groups(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户所属的所有群聊列表
    """
    group_service = GroupService()
    groups = await group_service.get_user_groups(user_id=current_user.id)
    
    return {"groups": groups}


@router.get("/groups/{group_id}/messages", response_model=List[GroupMessageResponse])
async def get_group_messages(
    group_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """
    获取群聊的历史消息
    """
    group_service = GroupService()
    
    # 验证用户是否属于该群聊
    is_member = await group_service.is_group_member(group_id, current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该群聊的成员"
        )
    
    messages = await group_service.get_messages(
        group_id=group_id,
        limit=limit,
        offset=offset
    )
    
    return messages


@router.post("/groups/{group_id}/send")
async def send_message(
    group_id: str,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user)
):
    """
    发送消息到群聊
    """
    from app.ws_manager.group_ws_manager import group_ws_manager
    from datetime import datetime
    
    group_service = GroupService()
    
    # 验证用户是否属于该群聊
    is_member = await group_service.is_group_member(group_id, current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该群聊的成员"
        )
    
    await group_service.send_message(
        group_id=group_id,
        user_id=current_user.id,
        message=request.message
    )
    
    # 通过WebSocket实时广播新消息
    await group_ws_manager.broadcast(group_id, {
        "type": "new_message",
        "message": {
            "sender_id": current_user.id,
            "sender_name": current_user.email.split('@')[0],
            "message": request.message,
            "message_type": "text",
            "created_at": str(int(datetime.now().timestamp() * 1000))
        }
    })
    
    return {"status": "success"}


@router.get("/groups/{group_id}/members")
async def get_group_members(
    group_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取群聊成员列表
    """
    group_service = GroupService()
    
    # 验证用户是否属于该群聊
    is_member = await group_service.is_group_member(group_id, current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该群聊的成员"
        )
    
    members = await group_service.get_group_members(group_id)
    return {"members": members}


@router.post("/groups/{group_id}/invite")
async def invite_students(
    group_id: str,
    request: InviteStudentsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    邀请学生加入群聊
    只有老师可以邀请
    """
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有老师可以邀请学生"
        )
    
    group_service = GroupService()
    await group_service.invite_students(
        group_id=group_id,
        student_ids=request.student_ids
    )
    
    return {"status": "success"}


@router.post("/groups/{group_id}/ai-ask")
async def ask_ai(
    group_id: str,
    request: AskAIRequest,
    current_user: User = Depends(get_current_user)
):
    """
    向AI助手提问（基于知识图谱）
    只有老师可以触发AI回答
    """
    from app.ws_manager.group_ws_manager import group_ws_manager
    from datetime import datetime
    import asyncio
    
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有老师可以使用AI助手"
        )
    
    group_service = GroupService()
    
    # 验证用户是否属于该群聊
    is_member = await group_service.is_group_member(group_id, current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该群聊的成员"
        )
    
    # 先广播"AI正在思考"的消息
    await group_ws_manager.broadcast(group_id, {
        "type": "ai_thinking",
        "message": "AI助手正在思考中..."
    })
    
    # 异步调用AI服务（不阻塞当前请求）
    asyncio.create_task(
        _process_ai_question(group_id, request.question, group_service, group_ws_manager)
    )
    
    return {"status": "success", "message": "AI正在思考中..."}


async def _process_ai_question(group_id: str, question: str, group_service, group_ws_manager):
    """
    异步处理AI问答并广播结果
    """
    from datetime import datetime
    
    try:
        # 调用AI服务获取答案
        print(f"🤖 开始处理AI问题: {question}")
        result = await group_service.ask_ai(group_id=group_id, question=question)
        
        # 检查发送是否成功
        if not result or not result.get('success'):
            raise Exception("消息发送失败")
        
        print(f"✅ AI回答已发送，使用方法: {result.get('method')}")
        
        # 等待消息完全写入Mattermost数据库
        # 根据发送方法调整延迟时间
        if result.get('method') == 'ai_assistant':
            # AI助手账户发送，需要更长时间
            await asyncio.sleep(2.0)
        else:
            # admin账户发送，相对较快
            await asyncio.sleep(1.5)
        
        # 验证消息是否已经可以被读取
        try:
            messages = await group_service.get_messages(group_id, limit=5)
            ai_message_found = any(
                msg.get('message_type') == 'ai_response' 
                for msg in messages
            )
            if not ai_message_found:
                print("⚠️ 警告：消息列表中未找到AI回答，再等待1秒")
                await asyncio.sleep(1.0)
        except Exception as verify_error:
            print(f"⚠️ 验证消息时出错: {verify_error}")
        
        # 广播AI回答已就绪
        print(f"📡 广播AI回答就绪事件")
        await group_ws_manager.broadcast(group_id, {
            "type": "ai_response_ready",
            "message": "AI助手已回答，请查看消息"
        })
        
    except Exception as e:
        print(f"❌ 处理AI问题时出错: {e}")
        import traceback
        print(traceback.format_exc())
        await group_ws_manager.broadcast(group_id, {
            "type": "ai_error",
            "message": f"AI回答失败: {str(e)}"
        })


@router.get("/users/students", response_model=List[dict])
async def get_students(
    current_user: User = Depends(get_current_user)
):
    """
    获取所有学生列表（用于创建群聊时选择）
    只有老师可以访问
    """
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有老师可以查看学生列表"
        )
    
    from app.models.user_model import User as UserModel
    
    students = await UserModel.filter(role="student").all()
    
    return [
        {
            "id": student.id,
            "username": student.email.split('@')[0],
            "email": student.email
        }
        for student in students
    ]


@router.post("/webhooks/mattermost")
async def mattermost_webhook(request: dict):
    """
    接收来自Mattermost的Webhook通知
    当有新消息时，Mattermost会调用此接口
    """
    # 这里会在阶段四实现WebSocket转发逻辑
    print(f"Received webhook from Mattermost: {request}")
    
    # TODO: 通过WebSocket转发给前端
    
    return {"status": "received"}


# ========== 新增功能的API端点 ==========

@router.post("/groups/{group_id}/upload-file")
async def upload_file(
    group_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传文件到群聊"""
    group_service = GroupService()
    
    # 验证用户是否属于该群聊
    is_member = await group_service.is_group_member(group_id, current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该群聊的成员"
        )
    
    # 读取文件数据
    file_data = await file.read()
    
    # 上传文件
    file_info = await group_service.upload_file(
        group_id=group_id,
        user_id=current_user.id,
        file_data=file_data,
        file_name=file.filename
    )
    
    return file_info


@router.get("/groups/{group_id}/files")
async def get_group_files(
    group_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取群聊的所有文件"""
    group_service = GroupService()
    
    # 验证用户是否属于该群聊
    is_member = await group_service.is_group_member(group_id, current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该群聊的成员"
        )
    
    files = await group_service.get_group_files(group_id)
    return files


@router.get("/groups/{group_id}/files/{file_id}/download")
async def download_file(
    group_id: str,
    file_id: str,
    token: str = None
):
    """下载群聊文件"""
    from fastapi.responses import StreamingResponse
    from app.api.deps import get_user_from_token
    import io
    
    # 从URL参数验证token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证token"
        )
    
    # 验证token并获取用户
    current_user = await get_user_from_token(token)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的token"
        )
    
    group_service = GroupService()
    
    # 验证用户是否属于该群聊
    is_member = await group_service.is_group_member(group_id, current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该群聊的成员"
        )
    
    # 获取文件内容
    file_data = await group_service.download_file(file_id)
    
    # 返回文件流
    return StreamingResponse(
        io.BytesIO(file_data['content']),
        media_type=file_data.get('mime_type', 'application/octet-stream'),
        headers={
            'Content-Disposition': f'attachment; filename="{file_data["name"]}"'
        }
    )


@router.post("/groups/{group_id}/search")
async def search_messages(
    group_id: str,
    request: SearchMessagesRequest,
    current_user: User = Depends(get_current_user)
):
    """搜索群聊消息"""
    group_service = GroupService()
    
    # 验证用户是否属于该群聊
    is_member = await group_service.is_group_member(group_id, current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该群聊的成员"
        )
    
    messages = await group_service.search_messages(
        group_id=group_id,
        query=request.query,
        user_id=current_user.id,
        limit=request.limit
    )
    
    return messages


@router.post("/groups/{group_id}/pin")
async def pin_message(
    group_id: str,
    request: PinMessageRequest,
    current_user: User = Depends(get_current_user)
):
    """置顶消息（仅老师）"""
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有老师可以置顶消息"
        )
    
    group_service = GroupService()
    await group_service.pin_message(request.post_id)
    
    return {"status": "success"}


@router.post("/groups/{group_id}/unpin")
async def unpin_message(
    group_id: str,
    request: PinMessageRequest,
    current_user: User = Depends(get_current_user)
):
    """取消置顶消息（仅老师）"""
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有老师可以取消置顶消息"
        )
    
    group_service = GroupService()
    await group_service.unpin_message(request.post_id)
    
    return {"status": "success"}


@router.get("/groups/{group_id}/pinned")
async def get_pinned_messages(
    group_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取置顶消息列表"""
    group_service = GroupService()
    
    # 验证用户是否属于该群聊
    is_member = await group_service.is_group_member(group_id, current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该群聊的成员"
        )
    
    messages = await group_service.get_pinned_messages(group_id)
    
    return messages


@router.post("/groups/{group_id}/send-with-mentions")
async def send_message_with_mentions(
    group_id: str,
    request: SendMessageWithMentionsRequest,
    current_user: User = Depends(get_current_user)
):
    """发送带@提及的消息"""
    group_service = GroupService()
    
    # 验证用户是否属于该群聊
    is_member = await group_service.is_group_member(group_id, current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该群聊的成员"
        )
    
    await group_service.send_message_with_mentions(
        group_id=group_id,
        user_id=current_user.id,
        message=request.message,
        mention_user_ids=request.mention_user_ids
    )
    
    return {"status": "success"}


@router.post("/groups/{group_id}/reply")
async def reply_to_message(
    group_id: str,
    request: ReplyMessageRequest,
    current_user: User = Depends(get_current_user)
):
    """回复消息（创建线程）"""
    group_service = GroupService()
    
    # 验证用户是否属于该群聊
    is_member = await group_service.is_group_member(group_id, current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该群聊的成员"
        )
    
    await group_service.reply_to_message(
        group_id=group_id,
        root_post_id=request.root_post_id,
        user_id=current_user.id,
        message=request.message
    )
    
    return {"status": "success"}


@router.get("/groups/{group_id}/thread/{post_id}")
async def get_thread(
    group_id: str,
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取消息线程"""
    group_service = GroupService()
    
    # 验证用户是否属于该群聊
    is_member = await group_service.is_group_member(group_id, current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该群聊的成员"
        )
    
    thread_messages = await group_service.get_thread(post_id)
    
    return thread_messages


@router.post("/groups/{group_id}/announcement")
async def set_announcement(
    group_id: str,
    request: SetAnnouncementRequest,
    current_user: User = Depends(get_current_user)
):
    """设置群公告（仅老师）"""
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有老师可以设置群公告"
        )
    
    group_service = GroupService()
    await group_service.set_announcement(group_id, request.announcement)
    
    return {"status": "success"}


@router.get("/groups/{group_id}/announcement")
async def get_announcement(
    group_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取群公告"""
    group_service = GroupService()
    
    # 验证用户是否属于该群聊
    is_member = await group_service.is_group_member(group_id, current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该群聊的成员"
        )
    
    announcement = await group_service.get_announcement(group_id)
    
    return {"announcement": announcement}


# ========== 邀请审核功能API ==========

@router.post("/groups/{group_id}/invite-student", response_model=GroupInvitationResponse)
async def student_invite_user(
    group_id: str,
    request: StudentInviteRequest,
    current_user: User = Depends(get_current_user)
):
    """
    学生邀请用户进入群聊（需要老师审核）
    """
    print(f"📝 学生邀请请求: 学生ID={current_user.id}, 角色={current_user.role}, 群聊ID={group_id}, 被邀请用户ID={request.invited_user_id}")
    
    if current_user.role != "student":
        print(f"❌ 权限检查失败: 用户角色={current_user.role}，不是学生")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以使用此邀请方式"
        )
    
    # 验证邀请者是否属于该群聊
    group_service = GroupService()
    is_member = await group_service.is_group_member(group_id, current_user.id)
    print(f"📋 群聊成员检查: 是否为成员={is_member}")
    if not is_member:
        print(f"❌ 成员检查失败: 用户不是群聊成员")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该群聊的成员"
        )
    
    try:
        invitation = await group_service.student_invite_user(
            group_id=group_id,
            inviter_id=current_user.id,
            invited_user_id=request.invited_user_id,
            reason=request.reason
        )
        print(f"✅ 邀请成功: 邀请ID={invitation['id']}")
        return invitation
    except Exception as e:
        print(f"❌ 邀请失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/groups/{group_id}/invite-teacher", response_model=dict)
async def teacher_invite_users(
    group_id: str,
    request: TeacherInviteRequest,
    current_user: User = Depends(get_current_user)
):
    """
    老师直接邀请用户进入群聊（无需审核）
    """
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有老师可以使用此邀请方式"
        )
    
    # 验证邀请者是否属于该群聊
    group_service = GroupService()
    is_member = await group_service.is_group_member(group_id, current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该群聊的成员"
        )
    
    try:
        result = await group_service.teacher_invite_users(
            group_id=group_id,
            teacher_id=current_user.id,
            user_ids=request.user_ids
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/groups/{group_id}/pending-invitations", response_model=PendingInvitationsResponse)
async def get_pending_invitations(
    group_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取群聊的待审核邀请列表（仅老师可见）
    """
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有老师可以查看待审核邀请"
        )
    
    group_service = GroupService()
    invitations = await group_service.get_pending_invitations(group_id)
    
    return {
        "invitations": invitations,
        "total_count": len(invitations)
    }


@router.post("/groups/invitations/{invitation_id}/review", response_model=GroupInvitationResponse)
async def review_invitation(
    invitation_id: str,
    request: ReviewInvitationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    老师审核邀请
    """
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有老师可以审核邀请"
        )
    
    try:
        group_service = GroupService()
        result = await group_service.review_invitation(
            invitation_id=invitation_id,
            teacher_id=current_user.id,
            approved=request.approved,
            reject_reason=request.reject_reason
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/user/invitations", response_model=dict)
async def get_user_invitations(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户收到的所有邀请
    """
    group_service = GroupService()
    invitations = await group_service.get_user_invitations(current_user.id)
    
    # 按状态分类
    pending = [inv for inv in invitations if inv['status'] == 'pending']
    approved = [inv for inv in invitations if inv['status'] == 'approved']
    rejected = [inv for inv in invitations if inv['status'] == 'rejected']
    
    return {
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "total_count": len(invitations)
    }
