# app/schemas/qa_schemas.py
"""
定义与问答功能相关的Pydantic模型。
"""
from typing import List, Optional, Union

from pydantic import BaseModel


class QuestionCreate(BaseModel):
    """用户提交问题的模型"""
    text: str
    force_regenerate: bool = False
    enable_tts: bool = True  # 默认启用TTS功能


class QuestionResponse(BaseModel):
    """提交问题后的即时响应模型"""
    question_id: str
    status: str
    detail: Optional[str] = None


class Source(BaseModel):
    """答案来源模型"""
    title: str
    node_id: str


class AnswerData(BaseModel):
    """包含答案和来源的完整数据模型"""
    answer: str
    sources: List[Source]


class AudioData(BaseModel):
    """音频数据模型"""
    audio_url: str
    duration: Optional[float] = None
    file_size: Optional[int] = None


class WebSocketResponse(BaseModel):
    """WebSocket推送消息的标准格式"""
    type: str  # e.g., "answer", "error", "audio_ready", "audio_generation_started"
    question_id: str
    data: Optional[Union[AnswerData, AudioData]] = None
    message: Optional[str] = None
    progress: Optional[int] = None  # 生成进度 0-100