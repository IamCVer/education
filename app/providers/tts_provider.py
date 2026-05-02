# app/providers/tts_provider.py
"""
TTS提供者模块，封装文本转语音功能。
已从 ChatTTS 迁移至阿里云 CosyVoice API。
"""
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, Union
import hashlib
import io

# 阿里云 DashScope SDK
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat

from app.core.config import settings

# 配置日志
logger = logging.getLogger(__name__)

# ============== 【已停用】ChatTTS 配置 ==============
# # ChatTTS服务的URL
# CHATTTS_SERVICE_URL = os.getenv("CHATTTS_SERVICE_URL", "http://chattts:9000")
# ============== 【已停用】ChatTTS 配置 结束 ==============

# 配置阿里云 API Key
dashscope.api_key = settings.DASHSCOPE_API_KEY

# 音色映射 (从 ChatTTS 迁移到阿里云 CosyVoice)
# ============== 【已停用】ChatTTS 音色映射 ==============
# VOICE_MAP = {
#     "male": "speaker_04",     # 男声
#     "female": "speaker_02",   # 女声
# }
# ============== 【已停用】ChatTTS 音色映射 结束 ==============

# 阿里云 CosyVoice 音色映射（根据官方文档）
# cosyvoice-v2 的音色带 _v2 后缀
VOICE_MAP = {
    "male": "longxiaochun_v2",       # 男声 - 知性积极女
    "female": "longanwen",           # 女声 - 优雅知性女 (ChatVRM 使用)
}
ALIYUN_MODEL = "cosyvoice-v2"  # 使用 cosyvoice-v2 模型（支持SSML，效果更好）


class CosyVoiceTTSProvider:
    """
    阿里云 CosyVoice TTS 服务提供者类
    
    负责通过阿里云 DashScope API 调用 CosyVoice 进行音频合成。
    采用单例模式确保配置一致性。
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化TTS提供者"""
        if not hasattr(self, '_initialized'):
            self.output_dir = Path("media/audio")   # 音频输出目录
            self._ensure_directories()
            self._initialized = True
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

# ============== 【已停用】ChatTTS Provider 类定义 ==============
# class ChatTTSProvider:
#     """
#     ChatTTS服务提供者类
#     
#     负责通过HTTP调用ChatTTS服务进行音频合成功能。
#     采用单例模式确保配置一致性。
#     """
#     
#     _instance = None
#     
#     def __new__(cls):
#         """单例模式实现"""
#         if cls._instance is None:
#             cls._instance = super().__new__(cls)
#         return cls._instance
#     
#     def __init__(self):
#         """初始化TTS提供者"""
#         if not hasattr(self, '_initialized'):
#             self.output_dir = Path("media/audio")   # 音频输出目录
#             self._ensure_directories()
#             self._initialized = True
#     
#     def _ensure_directories(self):
#         """确保必要的目录存在"""
#         self.output_dir.mkdir(parents=True, exist_ok=True)
# ============== 【已停用】ChatTTS Provider 类定义 结束 ==============

    async def generate_speech(
        self, 
        text: str, 
        model_path: Union[str, Path] = None,  # 保留参数以兼容旧接口，但不使用
        config_path: Union[str, Path] = None,  # 保留参数以兼容旧接口，但不使用
        output_filename: Optional[str] = None,
        temperature: float = 0.3,  # 保留参数以兼容旧接口，但 CosyVoice 不使用
        top_p: float = 0.7,  # 保留参数以兼容旧接口，但 CosyVoice 不使用
        top_k: int = 20,  # 保留参数以兼容旧接口，但 CosyVoice 不使用
        voice_type: str = "female"  # 音色类型: "male"（男声）或 "female"（女声）
    ) -> Path:
        """
        异步生成语音文件（主要接口函数）。
        调用阿里云 CosyVoice API 生成语音。
        """
        if not text or not text.strip():
            raise ValueError("输入文本不能为空")
        
        if output_filename is None:
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:10]
            output_filename = f"speech_{voice_type}_{text_hash}.mp3"
        
        output_path = self.output_dir / output_filename
        
        # 如果文件已存在，直接返回
        if output_path.exists():
            logger.info(f"使用已存在的音频文件: {output_path}")
            return output_path
        
        try:
            logger.info(f"调用阿里云 CosyVoice API 生成语音，文本长度: {len(text)} 字符，音色: {voice_type}")
            
            # 获取对应的音色ID
            voice_id = VOICE_MAP.get(voice_type, VOICE_MAP["female"])
            
            # 在线程池中执行同步API调用（dashscope SDK 是同步的）
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._call_cosyvoice_sync,
                text,
                voice_id
            )
            
            if not audio_data:
                raise ValueError("阿里云 CosyVoice API 没有返回音频数据")
            
            # 保存音频文件
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"语音合成完成，输出文件: {output_path}, 大小: {len(audio_data)} 字节")
            return output_path
                
        except Exception as e:
            logger.error(f"语音合成失败: {e}", exc_info=True)
            raise ValueError(f"阿里云 CosyVoice API 调用失败: {e}")
    
    def _call_cosyvoice_sync(self, text: str, voice_id: str) -> bytes:
        """
        同步调用阿里云 CosyVoice API（在线程池中执行）
        使用官方文档推荐的同步调用方式（tts_v2）
        """
        try:
            logger.info(f"🎙️ 开始调用 CosyVoice API - 模型: {ALIYUN_MODEL}, 音色: {voice_id}")
            logger.info(f"📝 待合成文本: {text[:50]}..." if len(text) > 50 else f"📝 待合成文本: {text}")
            logger.info(f"🔑 API Key 状态: {'已配置' if dashscope.api_key else '未配置'}")
            logger.info(f"🔑 API Key 前10位: {dashscope.api_key[:10] if dashscope.api_key else 'None'}...")
            
            # 根据官方文档，tts_v2 需要先实例化 SpeechSynthesizer，然后调用 call 方法
            # 注意:不传 format 参数，使用默认值 (22.05kHz mp3)
            synthesizer = SpeechSynthesizer(
                model=ALIYUN_MODEL,
                voice=voice_id
                # 不传 format 参数，使用默认值
            )
            logger.info(f"✅ SpeechSynthesizer 实例化成功 (model={ALIYUN_MODEL}, voice={voice_id}, format=default)")
            
            # 调用 API
            result = synthesizer.call(text)
            
            # 详细日志
            logger.info(f"📦 API 调用返回 - 类型: {type(result)}")
            if result is not None:
                logger.info(f"📦 result 属性: {dir(result) if hasattr(result, '__dict__') else 'N/A'}")
                if isinstance(result, bytes):
                    logger.info(f"📦 result 是 bytes,长度: {len(result)}")
                elif hasattr(result, 'audio_data'):
                    logger.info(f"📦 result 有 audio_data 属性")
                elif hasattr(result, 'get_audio_data'):
                    logger.info(f"📦 result 有 get_audio_data 方法")
            else:
                logger.error(f"❌ result 是 None!")
            
            # 根据测试结果,result 直接就是 bytes 类型的音频数据
            if isinstance(result, bytes) and len(result) > 0:
                logger.info(f"✅ CosyVoice API 调用成功,获取音频数据大小: {len(result)} bytes")
                return result
            elif result is None:
                logger.error(f"❌ CosyVoice API 返回 None，可能是 API Key 无效或服务未开通")
                logger.error(f"❌ 请检查: 1) API Key是否正确 2) CosyVoice服务是否开通 3) 账户余额是否充足")
                raise ValueError(f"CosyVoice API 返回 None，请检查 DASHSCOPE_API_KEY 是否正确且服务已开通")
            else:
                logger.error(f"❌ CosyVoice API 返回了非预期的类型或空数据: {type(result)}")
                raise ValueError(f"CosyVoice API 返回了非预期的类型: {type(result)}")
            
        except Exception as e:
            logger.error(f"❌ CosyVoice API 调用异常: {e}", exc_info=True)
            raise

# ============== 【已停用】ChatTTS generate_speech 方法 ==============
#     async def generate_speech(
#         self, 
#         text: str, 
#         model_path: Union[str, Path] = None,  # 保留参数以兼容旧接口，但不使用
#         config_path: Union[str, Path] = None,  # 保留参数以兼容旧接口，但不使用
#         output_filename: Optional[str] = None,
#         temperature: float = 0.3,
#         top_p: float = 0.7,
#         top_k: int = 20,
#         voice_type: str = "female"  # 音色类型: "male"（男声）或 "female"（女声）
#     ) -> Path:
#         """
#         异步生成语音文件（主要接口函数）。
#         调用ChatTTS服务生成语音。
#         """
#         if not text or not text.strip():
#             raise ValueError("输入文本不能为空")
#         
#         if output_filename is None:
#             text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:10]
#             output_filename = f"speech_{text_hash}.wav"
#         
#         output_path = self.output_dir / output_filename
#         
#         # 如果文件已存在，直接返回
#         if output_path.exists():
#             logger.info(f"使用已存在的音频文件: {output_path}")
#             return output_path
#         
#         try:
#             logger.info(f"调用ChatTTS服务生成语音，文本长度: {len(text)} 字符")
#             
#             # 调用ChatTTS服务（CPU模式下可能需要较长时间，设置10分钟超时）
#             async with httpx.AsyncClient(timeout=600.0) as client:
#                 response = await client.post(
#                     f"{CHATTTS_SERVICE_URL}/generate_audio",
#                     json={
#                         "text": text,
#                         "temperature": temperature,
#                         "top_p": top_p,
#                         "top_k": top_k,
#                         "voice_type": voice_type  # 传递音色类型
#                     }
#                 )
#                 
#                 if response.status_code != 200:
#                     raise ValueError(f"ChatTTS服务返回错误: {response.status_code} - {response.text}")
#                 
#                 # 保存音频文件
#                 with open(output_path, 'wb') as f:
#                     f.write(response.content)
#                 
#                 logger.info(f"语音合成完成，输出文件: {output_path}")
#                 return output_path
#                 
#         except httpx.RequestError as e:
#             logger.error(f"无法连接到ChatTTS服务: {e}", exc_info=True)
#             raise ValueError(f"ChatTTS服务不可用: {e}")
#         except Exception as e:
#             logger.error(f"语音合成失败: {e}", exc_info=True)
#             raise
# ============== 【已停用】ChatTTS generate_speech 方法 结束 ==============

# --- 为了方便调用而提供的便捷函数 ---

# 创建全局实例（单例模式）
tts_provider = CosyVoiceTTSProvider()

# ============== 【已停用】旧的全局实例创建 ==============
# tts_provider = ChatTTSProvider()
# ============== 【已停用】旧的全局实例创建 结束 ==============

async def generate_speech_async(
    text_to_speak: str, 
    model_path: Union[str, Path] = None,  # 保留参数以兼容旧接口，但不使用
    config_path: Union[str, Path] = None,  # 保留参数以兼容旧接口，但不使用
    output_filename: Optional[str] = None,
    temperature: float = 0.3,  # 保留参数以兼容旧接口，但 CosyVoice 不使用
    top_p: float = 0.7,  # 保留参数以兼容旧接口，但 CosyVoice 不使用
    top_k: int = 20,  # 保留参数以兼容旧接口，但 CosyVoice 不使用
    voice_type: str = "male"  # 音色类型: "male"（男声）或 "female"（女声）
) -> str:
    """
    异步语音生成便捷函数，返回文件路径字符串。
    适合在FastAPI等异步框架中直接调用。
    
    已从 ChatTTS 迁移至阿里云 CosyVoice API。
    """
    # 确保文本不为空
    if not text_to_speak or not text_to_speak.strip():
        raise ValueError("语音文本不能为空")
        
    # 生成语音（model_path和config_path参数会被忽略）
    file_path = await tts_provider.generate_speech(
        text=text_to_speak,
        output_filename=output_filename,
        temperature=temperature,  # CosyVoice 不使用，仅保留接口兼容
        top_p=top_p,  # CosyVoice 不使用，仅保留接口兼容
        top_k=top_k,  # CosyVoice 不使用，仅保留接口兼容
        voice_type=voice_type
    )
    
    # 验证生成的文件是否存在且有效
    path_obj = Path(file_path)
    if not path_obj.exists() or path_obj.stat().st_size < 100:  # 文件应至少有100字节
        logger.error(f"生成的语音文件无效或过小: {file_path}")
        raise ValueError(f"生成的语音文件无效: {file_path}")
        
    return str(file_path)

