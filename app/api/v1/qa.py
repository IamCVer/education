# app/api/v1/qa.py (最终正确版)
"""
提供知识问答的API端点和WebSocket通道。
"""
from typing import Annotated
import hashlib
from pathlib import Path

from fastapi import APIRouter, Depends, Form
from fastapi.responses import FileResponse
# vvvvvvvvvvvv 【核心修正：导入正确的依赖】 vvvvvvvvvvvv
from app.api.deps import get_current_user # <--- 恢复使用为HTTP设计的 get_current_user
# ^^^^^^^^^^^^ 【核心修正结束】 ^^^^^^^^^^^^
from app.models.user_model import User
from app.schemas import qa_schemas
from app.services import qa_service
from app.providers.tts_provider import generate_speech_async

router = APIRouter()


@router.post("/questions", response_model=qa_schemas.QuestionResponse)
async def create_question(
    question_in: qa_schemas.QuestionCreate,
    # vvvvvvvvvvvv 【核心修正：使用正确的认证依赖】 vvvvvvvvvvvv
    # HTTP POST接口，必须使用从Header获取Token的标准依赖项
    current_user: Annotated[User, Depends(get_current_user)],
    # ^^^^^^^^^^^^ 【核心修正结束】 ^^^^^^^^^^^^
):
    """
    接收用户提交的新问题，检查缓存或创建后台任务。
    """
    response = await qa_service.handle_new_question(
        question_in=question_in, user_id=current_user.id
    )
    return response

# WebSocket 端点已被正确地移至 main.py，此文件不再包含它

@router.post("/questions/{question_id}/generate-audio")
async def generate_audio_for_question(
    question_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    为指定的问题答案按需生成语音
    使用 chat 页面默认音色 (speaker_04)
    """
    response = await qa_service.generate_audio_on_demand(
        question_id=question_id, user_id=current_user.id, source="chat"
    )
    return response


@router.post("/tts/stream")
async def generate_tts_stream(
    current_user: Annotated[User, Depends(get_current_user)],
    text: str = Form(...),
    voice_type: str = Form("female"),  # 默认使用女声，可通过参数指定
):
    """
    为指定文本生成语音，直接返回音频流
    支持通过 voice_type 参数指定音色：'male'（男声）或 'female'（女声）
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🎤 TTS请求 - 文本: {text[:50]}..., 音色: {voice_type}")
    
    # 生成唯一文件名（基于文本内容的哈希和音色）
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:10]
    filename = f"tts_{voice_type}_{text_hash}.mp3"
    
    logger.info(f"📝 生成文件名: {filename}")
    
    # 生成语音
    audio_path_str = await generate_speech_async(
        text_to_speak=text,
        output_filename=filename,
        voice_type=voice_type
    )
    
    audio_path = Path(audio_path_str)
    
    logger.info(f"📁 音频文件路径: {audio_path}")
    logger.info(f"✅ 文件存在: {audio_path.exists()}, 大小: {audio_path.stat().st_size if audio_path.exists() else 0} bytes")
    
    # 返回音频文件
    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename=filename
    )