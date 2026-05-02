# app/providers/llm_provider.py (最终修正版 - 拥抱OpenAI兼容模式)
"""
通过LangChain的ChatOpenAI类，连接到阿里云通义千问的OpenAI兼容API端点。
这是官方推荐的最佳实践，可以确保最高的稳定性和兼容性。
"""
from langchain_openai import ChatOpenAI
from app.core.config import settings

# --- 实例化完全兼容的、由LangChain官方支持的模型 ---

# 轻量级、高速模型，用于路由、分类等简单任务
turbo_llm = ChatOpenAI(
    model=settings.QWEN_TURBO_MODEL_NAME,
    api_key=settings.QWEN_API_KEY,
    base_url=settings.QWEN_BASE_URL,
    temperature=0.0,  # 路由和分析任务需要更确定的输出
    max_tokens=2048,
    timeout=60,  # API请求超时时间：60秒
    max_retries=3,  # 失败后最多重试3次
)

# 功能强大的模型，用于生成、合成等复杂任务
max_llm = ChatOpenAI(
    model=settings.QWEN_MAX_MODEL_NAME,
    api_key=settings.QWEN_API_KEY,
    base_url=settings.QWEN_BASE_URL,
    temperature=0.7,  # 生成任务需要一些创造性
    max_tokens=4096,
    timeout=90,  # API请求超时时间：90秒（生成任务可能需要更长时间）
    max_retries=3,  # 失败后最多重试3次
)