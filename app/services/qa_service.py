# app/services/qa_service.py
"""
编排问答业务的初始流程：缓存检查与任务入队。
"""
import json
from uuid import uuid4
from pathlib import Path

from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import settings
from app.pubsub import redis_pubsub
from app.schemas.qa_schemas import QuestionCreate, AnswerData, AudioData, WebSocketResponse
from app.services.caching_service import get_cache_service
from app.providers.tts_provider import generate_speech_async
from app.db.redis_client import get_redis_client


async def handle_new_question(question_in: QuestionCreate, user_id: int) -> dict:
    """
    处理新的用户问题。
    它首先检查语义缓存，如果命中，则直接返回结果；
    如果未命中或被要求强制重新生成，则将任务推送到ARQ队列。
    """
    task_id = str(uuid4())

    # 在函数内部获取已初始化的cache_service实例
    cache_service = get_cache_service()

    # 1. 检查缓存（除非用户要求强制重新生成）
    if not question_in.force_regenerate:
        cached_result = await cache_service.get_cached_answer(question_in.text)
        if cached_result:
            print(f"---API: 缓存命中，问题: '{question_in.text}'---")
            answer_data = AnswerData(
                answer=cached_result["answer"],
                sources=cached_result["sources"]
            )

            # 通过Pub/Sub实时推送缓存结果
            ws_response = WebSocketResponse(
                type="answer",
                question_id=task_id,
                data=answer_data
            )
            await redis_pubsub.publish_message({
                "user_id": user_id,
                "payload": ws_response.dict()
            })
            
            # 存储缓存答案到Redis，以便后续按需生成音频
            await store_question_answer(task_id, cached_result["answer"], cached_result["sources"])
            print("缓存答案已存储，可按需生成TTS")
            
            return {"question_id": task_id, "status": "completed_from_cache"}

    # 2. 缓存未命中或强制重新生成，则创建后台任务
    print(f"---API: 缓存未命中或强制重新生成，正在将任务推入队列...---")
    redis_settings = RedisSettings(host=settings.REDIS_HOST)
    arq_pool = await create_pool(redis_settings)
    await arq_pool.enqueue_job(
        "process_question_task",
        task_id,
        user_id,
        question_in.text,
        False,  # 默认不生成TTS，需要用户主动点击
    )
    return {"question_id": task_id, "status": "processing"}


async def generate_cached_tts(task_id: str, user_id: int, answer_text: str):
    """
    为缓存的答案生成TTS音频
    """
    # 发送TTS开始消息
    ws_response = WebSocketResponse(
        type="audio_generation_started",
        question_id=task_id,
        message="正在生成语音..."
    )
    await redis_pubsub.publish_message({
        "user_id": user_id,
        "payload": ws_response.dict()
    })

    # 生成音频文件（使用男声）
    audio_file_str = await generate_speech_async(
        text_to_speak=answer_text,
        output_filename=f"cached_answer_{task_id}.wav",
        voice_type="male"
    )
    
    # 转换为Path对象
    audio_file = Path(audio_file_str)

    # 计算音频文件信息
    file_size = audio_file.stat().st_size if audio_file.exists() else 0
    audio_url = f"/media/audio/{audio_file.name}"

    # 发送音频就绪消息
    ws_response = WebSocketResponse(
        type="audio_ready",
        question_id=task_id,
        data=AudioData(
            audio_url=audio_url,
            file_size=file_size
        )
    )
    await redis_pubsub.publish_message({
        "user_id": user_id,
        "payload": ws_response.dict()
    })


async def store_question_answer(question_id: str, answer_text: str, sources: list):
    """
    存储问题ID和对应的答案到Redis，用于后续按需生成音频
    """
    try:
        redis_client = get_redis_client()
        data = {
            "answer": answer_text,
            "sources": sources
        }
        # 存储到Redis，设置24小时过期
        await redis_client.setex(
            f"question_answer:{question_id}", 
            86400,  # 24小时
            json.dumps(data, ensure_ascii=False)
        )
        print(f"已存储问题答案到Redis: {question_id}")
    except Exception as e:
        print(f"存储问题答案到Redis失败: {e}")
        # 降级到内存缓存
        if not hasattr(store_question_answer, '_fallback_cache'):
            store_question_answer._fallback_cache = {}
        store_question_answer._fallback_cache[question_id] = {
            "answer": answer_text,
            "sources": sources
        }

async def generate_audio_on_demand(question_id: str, user_id: int, source: str = "chat") -> dict:
    """
    按需为指定问题ID生成音频
    source: 请求来源 ("chat" 或 "chatvrm")，用于选择对应音色
    """
    # 从Redis中获取答案
    try:
        redis_client = get_redis_client()
        cached_data = await redis_client.get(f"question_answer:{question_id}")
        
        if cached_data:
            answer_data = json.loads(cached_data)
        else:
            # 尝试从降级缓存获取
            if (hasattr(store_question_answer, '_fallback_cache') and 
                question_id in store_question_answer._fallback_cache):
                answer_data = store_question_answer._fallback_cache[question_id]
            else:
                return {"error": "问题答案未找到，请重新提问"}
        
        answer_text = answer_data["answer"]
        print(f"找到问题答案: {question_id}")
        
    except Exception as e:
        print(f"获取问题答案失败: {e}")
        return {"error": "获取问题答案时发生错误，请重新提问"}
    
    try:
        # 发送TTS开始消息
        ws_response = WebSocketResponse(
            type="audio_generation_started",
            question_id=question_id,
            message="正在生成语音..."
        )
        await redis_pubsub.publish_message({
            "user_id": user_id,
            "payload": ws_response.dict()
        })
        print(f"✅ 已发送TTS开始消息，用户ID: {user_id}, 问题ID: {question_id}")

        # 生成音频文件
        # 根据来源选择音色：chat页面使用男声，chatvrm使用女声
        voice_type = "female" if source == "chatvrm" else "male"
        print(f"🔊 按需生成TTS音频，问题ID: {question_id}, 文本长度: {len(answer_text)}, 来源: {source}, 音色: {voice_type}")
        audio_file_str = await generate_speech_async(
            text_to_speak=answer_text,
            output_filename=f"ondemand_{question_id}.wav",
            voice_type=voice_type
        )
        
        if not audio_file_str:
            raise ValueError("TTS生成过程未能返回有效的文件路径字符串。")

        audio_file = Path(audio_file_str)
        file_size = audio_file.stat().st_size if audio_file.exists() else 0
        audio_url = f"/media/audio/{audio_file.name}"

        # 发送音频就绪消息
        ws_response = WebSocketResponse(
            type="audio_ready",
            question_id=question_id,
            data=AudioData(
                audio_url=audio_url,
                file_size=file_size
            )
        )
        await redis_pubsub.publish_message({
            "user_id": user_id,
            "payload": ws_response.dict()
        })
        
        print(f"按需TTS生成完成，问题ID: {question_id}")
        return {"status": "success", "audio_url": audio_url}
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ 按需TTS生成失败，问题ID: {question_id}, 错误: {e}")
        print(f"错误详情:\n{error_details}")
        
        # 发送TTS失败消息
        ws_response = WebSocketResponse(
            type="audio_error",
            question_id=question_id,
            message=f"语音生成失败: {str(e)}"
        )
        await redis_pubsub.publish_message({
            "user_id": user_id,
            "payload": ws_response.dict()
        })
        
        return {"error": f"语音生成失败: {str(e)}"}

