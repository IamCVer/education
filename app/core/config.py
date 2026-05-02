# app/core/config.py (修正版)
"""
应用配置中心，通过Pydantic加载和管理所有环境变量。
"""
from pydantic_settings import BaseSettings
from pathlib import Path
import os


class Settings(BaseSettings):
    """
    应用配置类，自动从环境变量或.env文件加载配置。
    """
    # 数据库配置
    DATABASE_URL: str
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str
    REDIS_HOST: str

    # JWT 安全配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Qwen API 配置
    QWEN_API_KEY: str
    QWEN_TURBO_MODEL_NAME: str = "qwen-turbo"
    QWEN_MAX_MODEL_NAME: str = "qwen-max"
    # vvvvvvvvvvvv 新增配置项 vvvvvvvvvvvv
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    # ^^^^^^^^^^^^ 新增配置项 ^^^^^^^^^^^^
    
    # 阿里云 TTS (CosyVoice) 配置
    DASHSCOPE_API_KEY: str  # 阿里云 DashScope API Key
    COSYVOICE_MODEL: str = "cosyvoice-v2"  # CosyVoice 模型版本（v2支持SSML，效果更好）
    COSYVOICE_VOICE_MALE: str = "longxiaochun_v2"  # 男声音色
    COSYVOICE_VOICE_FEMALE: str = "longxiaoxuan_v2"  # 女声音色

    # Qdrant Vector Database 配置
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    DISABLE_SEMANTIC_CACHE: bool = False
    
    # MediaCMS 配置
    mediacms_url: str = "http://mediacms:80"
    mediacms_api_url: str = "http://mediacms:80/api/v1"
    mediacms_admin_token: str = ""
    mediacms_admin_password: str = ""
    mediacms_secret_key: str = ""
    
    # ChatTTS 服务配置
    chattts_service_url: str = "http://chattts:9000"
    
    # 阿里云OSS 配置
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_endpoint: str = "oss-cn-hangzhou.aliyuncs.com"
    oss_bucket_name: str = "education-videos"
    
    # 🆕 模型文件路径配置
    MODEL_PATH: str = "./models"


    # API 基础URL (直接指向后端端口，绕过Nginx代理以避免流媒体问题)
    BASE_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
    
    # 🆕 计算绝对路径
    @property
    def model_root_path(self) -> Path:
        """返回模型根目录的绝对路径"""
        path = Path(self.MODEL_PATH)
        if not path.is_absolute():
            # 如果是相对路径，相对于项目根目录（/code 在容器中或项目根）
            path = Path(__file__).parent.parent.parent / path
        return path.resolve()
    
    @property
    def chattts_model_path(self) -> Path:
        """ChatTTS模型路径"""
        return self.model_root_path / "chattts"
    
    @property
    def tts_voices_path(self) -> Path:
        """TTS音色库路径"""
        return self.model_root_path / "tts_voices"
    
    @property
    def embeddings_cache_path(self) -> Path:
        """嵌入模型缓存路径"""
        return self.model_root_path / "embeddings"
    
    @property
    def qdrant_storage_path(self) -> Path:
        """Qdrant数据库存储路径"""
        return self.model_root_path / "qdrant_storage"
    
    @property
    def huggingface_cache_path(self) -> Path:
        """HuggingFace模型缓存路径"""
        return self.model_root_path / "huggingface_cache"
    
    @property
    def graphrag_data_path(self) -> Path:
        """GraphRAG数据路径"""
        return self.model_root_path / "graphrag_data"


settings = Settings()
