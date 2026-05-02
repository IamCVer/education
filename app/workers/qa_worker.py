# app/workers/qa_worker.py (最终正确版)
"""
[层] 异步任务层
[职责] 定义ARQ Worker的配置和任务函数，并为其配置独立的数据库和Redis生命周期。
"""
import traceback
import sys
from pathlib import Path  # <--- 【修复 1: 添加缺失的导入】
from tortoise import Tortoise

from app.agents import qa_agent
from app.data_access import qa_history_db
from app.pubsub import redis_pubsub
from app.schemas.qa_schemas import AnswerData, AudioData, WebSocketResponse
from app.services.caching_service import init_cache_service, get_cache_service
from app.providers.tts_provider import generate_speech_async
from app.services.qa_service import store_question_answer
from app.core.config import settings
from arq.connections import RedisSettings
from app.db.tortoise_config import TORTOISE_ORM_CONFIG
from app.db.redis_client import init_redis_pool, close_redis_pool

async def on_startup(ctx):
    """
    Worker启动时执行的函数：初始化数据库、缓存服务和Redis客户端。
    """
    print("Worker starting up...")
    await Tortoise.init(config=TORTOISE_ORM_CONFIG)
    await init_cache_service()
    await init_redis_pool()
    print("Worker database, cache, and Redis client initialized.")


async def on_shutdown(ctx):
    """
    Worker关闭时执行的函数：关闭数据库和Redis连接。
    """
    print("Worker shutting down...")
    await Tortoise.close_connections()
    await close_redis_pool()
    print("Worker database and Redis connections closed.")


async def process_question_task(ctx, task_id: str, user_id: int, question_text: str, enable_tts: bool = True):
    """
    ARQ任务：处理一个问答请求。
    """
    print(f"Processing task {task_id} for user {user_id}: {question_text}")
    try:
        cache_service = get_cache_service()
        
        # 首先检查缓存
        cached_result = await cache_service.get_cached_answer(question_text)
        
        if cached_result:
            # 使用缓存的答案
            print(f"Using cached answer for task {task_id}")
            answer = cached_result["answer"]
            sources = cached_result["sources"]
            cached_audio_url = cached_result.get("audio_url")
            cached_audio_size = cached_result.get("audio_file_size", 0)
            
            # 1. 立即发送文本答案
            ws_response = WebSocketResponse(
                type="answer", question_id=task_id,
                data=AnswerData(answer=answer, sources=sources)
            )
            await redis_pubsub.publish_message({
                "user_id": user_id,
                "payload": ws_response.dict()
            })
            print(f"Task {task_id} cached text answer completed and published.")
            
            # 存储答案到Redis缓存，以便后续按需生成音频
            await store_question_answer(task_id, answer, sources)
            
            # 2. 如果有缓存的音频文件，直接发送
            if cached_audio_url and enable_tts:
                # 验证音频文件是否仍然存在
                from pathlib import Path
                audio_file_path = Path(f"/code/media/audio/{Path(cached_audio_url).name}")
                if audio_file_path.exists():
                    ws_response = WebSocketResponse(
                        type="audio_ready",
                        question_id=task_id,
                        data=AudioData(
                            audio_url=cached_audio_url,
                            file_size=cached_audio_size
                        )
                    )
                    await redis_pubsub.publish_message({
                        "user_id": user_id,
                        "payload": ws_response.dict()
                    })
                    print(f"Task {task_id} cached audio sent: {cached_audio_url}")
                else:
                    # 音频文件不存在，重新生成
                    print(f"Cached audio file missing, regenerating for task {task_id}")
                    await process_tts_task(task_id, user_id, question_text, answer, sources)
            elif enable_tts:
                # 没有缓存的音频，生成新的
                await process_tts_task(task_id, user_id, question_text, answer, sources)
        else:
            # 没有缓存，正常处理
            print(f"No cache found, processing normally for task {task_id}")
            agent_result = await qa_agent.run_agent(question_text)
            answer = agent_result["answer"]
            sources = agent_result["sources"]

            await qa_history_db.create_qa_record(
                user_id=user_id, question=question_text,
                answer=answer, sources=sources
            )
            
            # 不在这里缓存，等TTS完成后一次性缓存所有信息

            # 1. 立即发送文本答案
            ws_response = WebSocketResponse(
                type="answer", question_id=task_id,
                data=AnswerData(answer=answer, sources=sources)
            )
            await redis_pubsub.publish_message({
                "user_id": user_id,
                "payload": ws_response.dict()
            })
            print(f"Task {task_id} text answer completed and published.")
            
            # 存储答案到Redis缓存，以便后续按需生成音频
            await store_question_answer(task_id, answer, sources)

            # 2. 如果启用TTS，生成音频，否则直接缓存
            if enable_tts:
                await process_tts_task(task_id, user_id, question_text, answer, sources)
            else:
                # 没有启用TTS，只缓存文本答案
                await cache_service.set_cached_answer(
                    text=question_text, answer=answer, sources=sources
                )

    except Exception as e:
        print(f"Error processing task {task_id}: {e}", file=sys.stderr, flush=True)
        traceback.print_exc()
        ws_response = WebSocketResponse(
            type="error", question_id=task_id,
            message="处理您的问题时发生内部错误。"
        )
        await redis_pubsub.publish_message({
            "user_id": user_id,
            "payload": ws_response.dict()
        })


async def process_tts_task(task_id: str, user_id: int, question_text: str, answer_text: str, sources: list):
    """
    处理TTS音频生成任务，并更新缓存
    """
    try:
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
        print(f"Starting TTS generation for task {task_id} with male voice")
        audio_file_str = await generate_speech_async(
            text_to_speak=answer_text,
            output_filename=f"answer_{task_id}.wav",
            voice_type="male"  # 使用男声
        )
        
        if not audio_file_str:
            raise ValueError("TTS生成过程未能返回有效的文件路径字符串。")

        # --- 【修复 2: 将返回的字符串路径转换为Path对象】 ---
        audio_file = Path(audio_file_str)

        # --- 【修复 3: 现在可以使用Path对象的方法了】 ---
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
        print(f"TTS generation completed for task {task_id}: {audio_file}")
        
        # 更新缓存，包含音频文件信息
        try:
            cache_service = get_cache_service()
            await cache_service.set_cached_answer(
                text=question_text, 
                answer=answer_text, 
                sources=sources,
                audio_url=audio_url,
                audio_file_size=file_size
            )
            print(f"Cache updated with audio info for question: {question_text[:50]}...")
        except Exception as cache_error:
            print(f"Failed to update cache with audio info: {cache_error}")

    except Exception as e:
        print(f"Error generating TTS for task {task_id}: {e}", file=sys.stderr, flush=True)
        traceback.print_exc()
        
        # TTS失败时，仍然缓存文本答案
        try:
            cache_service = get_cache_service()
            await cache_service.set_cached_answer(
                text=question_text, 
                answer=answer_text, 
                sources=sources
            )
            print(f"Cached text answer without audio for question: {question_text[:50]}...")
        except Exception as cache_error:
            print(f"Failed to cache answer after TTS failure: {cache_error}")
        
        # 发送TTS失败警告消息
        ws_response = WebSocketResponse(
            type="audio_error",
            question_id=task_id,
            message="语音生成失败，但文本答案正常。"
        )
        await redis_pubsub.publish_message({
            "user_id": user_id,
            "payload": ws_response.dict()
        })


class WorkerSettings:
    """ARQ Worker的配置"""
    functions = [process_question_task]
    on_startup = on_startup
    on_shutdown = on_shutdown
    redis_settings = RedisSettings(host=settings.REDIS_HOST)
    job_timeout = 600  # 增加任务超时时间到10分钟，应对API限流
    max_jobs = 5  # 限制最大并发任务数，避免触发API限流

