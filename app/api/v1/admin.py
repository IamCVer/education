# app/api/v1/admin.py
"""
提供管理性的API端点，例如手动触发知识图谱的索引构建、用户管理、对话历史查询等。
"""
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from qdrant_client import models
from pydantic import BaseModel

from app.data_access.graph_db import graph_db
from app.core.config import settings
from app.services.caching_service import get_cache_service
from app.data_access.user_db import get_all_users, get_user_by_id, create_user_db, update_user_db, delete_user_db
from app.data_access.qa_history_db import get_qa_histories_by_user, get_qa_history_by_id, delete_qa_history
from app.api.deps import get_current_user, get_admin_user
from app.models.user_model import User

router = APIRouter()

# ============ Pydantic 模型 ============
class UserCreateRequest(BaseModel):
    email: str
    password: str
    role: str = "user"

class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

# 创建一个固定的命名空间UUID，确保哈希过程是可复现的
NAMESPACE_UUID = uuid.NAMESPACE_DNS


# ============ 用户管理 API ============
@router.get("/users")
async def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: str = Query(""),
    current_user: User = Depends(get_admin_user)
):
    """获取用户列表（分页）"""
    try:
        users = await get_all_users()
        
        # 搜索过滤
        if search:
            users = [u for u in users if search.lower() in u.username.lower() or search.lower() in u.email.lower()]
        
        total = len(users)
        start = (page - 1) * size
        end = start + size
        items = users[start:end]
        
        return {
            "items": [
                {
                    "id": u.id,
                    "email": u.email,
                    "role": u.role,
                    "created_at": u.created_at.isoformat() if u.created_at else None
                }
                for u in items
            ],
            "total": total,
            "page": page,
            "size": size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_admin_user)
):
    """获取单个用户详情"""
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.post("/users")
async def create_user(
    user_data: UserCreateRequest,
    current_user: User = Depends(get_admin_user)
):
    """创建新用户"""
    try:
        from app.core.security import get_password_hash
        hashed_password = get_password_hash(user_data.password)
        
        new_user = await create_user_db(
            email=user_data.email,
            hashed_password=hashed_password,
            role=user_data.role
        )
        
        return {
            "id": new_user.id,
            "email": new_user.email,
            "role": new_user.role,
            "message": "用户创建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建用户失败: {str(e)}")


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    current_user: User = Depends(get_admin_user)
):
    """更新用户信息"""
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        update_data = user_data.dict(exclude_unset=True)
        updated_user = await update_user_db(user_id, **update_data)
        
        return {
            "id": updated_user.id,
            "email": updated_user.email,
            "role": updated_user.role,
            "message": "用户更新成功"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新用户失败: {str(e)}")


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_admin_user)
):
    """删除用户"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        await delete_user_db(user_id)
        return {"message": "用户删除成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"删除用户失败: {str(e)}")


# ============ 对话历史管理 API ============
@router.get("/conversations")
async def get_conversations(
    user_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=10000),
    is_export: bool = Query(False, description="是否为导出操作"),
    current_user: User = Depends(get_admin_user)
):
    """获取对话历史（可按用户ID过滤，size最大10000用于导出）"""
    try:
        if user_id:
            histories = await get_qa_histories_by_user(user_id)
        else:
            # 如果没有指定用户ID，返回所有对话（需要实现相应的数据库方法）
            histories = []
        
        total = len(histories)
        start = (page - 1) * size
        end = start + size
        items = histories[start:end]
        
        result = {
            "items": [
                {
                    "id": h.id,
                    "user_id": h.user_id,
                    "question": h.question_text,
                    "answer": h.answer_text,
                    "context": h.sources if hasattr(h, 'sources') else None,
                    "created_at": h.created_at.isoformat() if h.created_at else None
                }
                for h in items
            ],
            "total": total,
            "page": page,
            "size": size
        }
        
        # 如果是导出操作，创建通知
        if is_export and user_id:
            from app.services.notification_service import notify_data_export
            try:
                # 获取被导出用户的信息
                target_user = await get_user_by_id(user_id)
                target_username = target_user.email.split('@')[0] if target_user else f"用户{user_id}"
                
                # 创建通知（记录到当前操作的管理员账户）
                await notify_data_export(
                    username=current_user.email.split('@')[0],
                    user_id=current_user.id,
                    data_type=f"用户 {target_username} 的对话历史"
                )
            except Exception as notify_error:
                # 通知创建失败不应影响主流程
                print(f"创建导出通知失败: {notify_error}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话历史失败: {str(e)}")


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_admin_user)
):
    """获取单条对话详情"""
    history = await get_qa_history_by_id(conversation_id)
    if not history:
        raise HTTPException(status_code=404, detail="对话记录不存在")
    
    return {
        "id": history.id,
        "user_id": history.user_id,
        "question": history.question_text,
        "answer": history.answer_text,
        "context": history.sources if hasattr(history, 'sources') else None,
        "created_at": history.created_at.isoformat() if history.created_at else None
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_admin_user)
):
    """删除对话记录"""
    history = await get_qa_history_by_id(conversation_id)
    if not history:
        raise HTTPException(status_code=404, detail="对话记录不存在")
    
    try:
        await delete_qa_history(conversation_id)
        return {"message": "对话记录删除成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"删除对话记录失败: {str(e)}")


# ============ 知识图谱索引 API ============
@router.post("/index-knowledge-graph", status_code=200)
async def index_knowledge_graph():
    """
    从Neo4j中提取所有Concept节点，将其向量化并存入Qdrant。
    """
    print("---ADMIN: 开始索引知识图谱到Qdrant...---")
    if settings.DISABLE_SEMANTIC_CACHE:
        raise HTTPException(status_code=400, detail="当前部署已关闭语义缓存，无法执行Qdrant索引。")
    try:
        # 1. 从Neo4j获取所有概念节点
        query = "MATCH (n:Concept) RETURN n.id AS node_id, n.name AS name, n.description AS description"
        nodes = await graph_db.execute_query(query)

        if not nodes:
            raise HTTPException(status_code=404, detail="在Neo4j中未找到任何:Concept节点进行索引。")

        # 2. 准备数据点以存入Qdrant
        cache_service = get_cache_service()
        points_to_upsert = []

        texts_to_encode = [f"{node['name']}: {node['description']}" for node in nodes]
        vectors = cache_service.embedding_model.encode(texts_to_encode).tolist()

        for i, node in enumerate(nodes):
            # vvvvvvvvvvvv 这是最关键的修正 vvvvvvvvvvvv
            # 使用uuid.uuid5从节点ID生成一个确定性的、格式正确的UUID
            point_id = str(uuid.uuid5(NAMESPACE_UUID, node['node_id']))
            # ^^^^^^^^^^^^ 这是最关键的修正 ^^^^^^^^^^^^

            point = models.PointStruct(
                id=point_id,
                vector=vectors[i],
                payload={
                    "node_id": node['node_id'],
                    "name": node['name'],
                    "description": node['description']
                }
            )
            points_to_upsert.append(point)

        # 3. 批量写入Qdrant
        await cache_service.client.upsert(
            collection_name="qa_cache_collection",
            points=points_to_upsert,
            wait=True
        )

        message = f"成功索引 {len(points_to_upsert)} 个节点到Qdrant。"
        print(f"---ADMIN: {message}---")
        return {"detail": message}

    except Exception as e:
        print(f"---ADMIN: 索引过程中发生错误: {e}---")
        raise HTTPException(status_code=500, detail=f"索引失败: {e}")
