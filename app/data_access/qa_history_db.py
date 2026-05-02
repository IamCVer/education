# app/data_access/qa_history_db.py
"""
封装与问答历史记录表的数据库交互逻辑。
"""
from typing import List, Dict, Optional

from app.models.qa_history_model import QAHistory


async def create_qa_record(
    user_id: int, question: str, answer: str, sources: List[Dict]
) -> QAHistory:
    """在数据库中创建一条新的问答记录"""
    record = await QAHistory.create(
        user_id=user_id,
        question_text=question,
        answer_text=answer,
        sources=sources,
    )
    return record


async def get_qa_histories_by_user(user_id: int, skip: int = 0, limit: int = 100) -> List[QAHistory]:
    """
    获取指定用户的所有问答历史记录（分页）。

    Args:
        user_id: 用户ID。
        skip: 跳过的记录数。
        limit: 返回的最大记录数。

    Returns:
        问答历史记录列表。
    """
    return await QAHistory.filter(user_id=user_id).order_by('-created_at').offset(skip).limit(limit)


async def get_qa_history_by_id(history_id: int) -> Optional[QAHistory]:
    """
    通过ID获取问答历史记录。

    Args:
        history_id: 问答历史记录ID。

    Returns:
        问答历史记录实例，如果不存在则返回None。
    """
    return await QAHistory.get_or_none(id=history_id)


async def delete_qa_history(history_id: int) -> bool:
    """
    删除问答历史记录。

    Args:
        history_id: 问答历史记录ID。

    Returns:
        如果删除成功返回True，否则返回False。
    """
    record = await QAHistory.get_or_none(id=history_id)
    if not record:
        return False
    
    await record.delete()
    return True