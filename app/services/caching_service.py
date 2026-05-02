# app/services/caching_service.py
"""
封装与语义缓存（Qdrant向量数据库）的交互逻辑，并内置异步连接重试机制。
"""
import asyncio
import json
import uuid
import os
from typing import Optional, List, Dict, Any

from qdrant_client import AsyncQdrantClient, models

from app.core.config import settings

# 🆕 设置HuggingFace缓存目录
os.environ["HF_HOME"] = str(settings.huggingface_cache_path)
os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(settings.embeddings_cache_path)

# 确保缓存目录存在
settings.embeddings_cache_path.mkdir(parents=True, exist_ok=True)
settings.huggingface_cache_path.mkdir(parents=True, exist_ok=True)
settings.qdrant_storage_path.mkdir(parents=True, exist_ok=True)

COLLECTION_NAME = "qa_cache_collection"
# 创建一个固定的命名空间UUID，确保哈希过程是可复现的
NAMESPACE_UUID = uuid.NAMESPACE_DNS


class NoOpSemanticCache:
    """
    关闭语义缓存时使用的空实现。
    保持与真实缓存服务的调用接口兼容，但不做任何向量检索或写入。
    """

    def __init__(self):
        self.client = None
        self.collection_initialized = False
        self._embedding_model = None

    async def initialize(self, retries: int = 0, delay: int = 0):
        print("Semantic Cache is disabled. Using no-op cache service.")

    @property
    def embedding_model(self):
        raise RuntimeError("Semantic cache is disabled.")

    def _get_embedding_model(self):
        raise RuntimeError("Semantic cache is disabled.")

    async def get_cached_answer(self, text: str, threshold: float = 0.95) -> Optional[Dict]:
        return None

    async def set_cached_answer(
        self,
        text: str,
        answer: str,
        sources: List[Dict],
        audio_url: Optional[str] = None,
        audio_file_size: int = 0
    ):
        return None


class SemanticCache:
    """
    管理与Qdrant向量数据库的所有交互，包括连接、初始化、查询和写入。
    """

    def __init__(self):
        # 🆕 根据配置使用本地Qdrant或远程连接
        if settings.QDRANT_HOST == "localhost" or settings.QDRANT_HOST == "127.0.0.1":
            # 本地开发使用文件数据库
            print(f"使用本地Qdrant数据库: {settings.qdrant_storage_path}")
            self.client = AsyncQdrantClient(path=str(settings.qdrant_storage_path))
        else:
            # Docker环境使用网络连接
            print(f"连接到Qdrant服务器: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
            self.client = AsyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

        # 延迟加载嵌入模型，避免启动时的长时间等待
        self._embedding_model = None

        self.collection_initialized = False

    def _get_embedding_model(self):
        """延迟加载嵌入模型"""
        if self._embedding_model is None:
            print("Loading embedding model (this may take a moment)...")
            from sentence_transformers import SentenceTransformer
            self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            print("✓ Embedding model loaded")
        return self._embedding_model

    @property
    def embedding_model(self):
        return self._get_embedding_model()

    async def initialize(self, retries: int = 10, delay: int = 5):
        """
        异步初始化方法，用于连接并确保集合存在。
        内置了重试逻辑，以等待Qdrant服务完全就绪。
        """
        print("Attempting to initialize Semantic Cache with Qdrant...")
        for attempt in range(retries):
            try:
                # 尝试与Qdrant通信，例如获取集合列表
                collections_response = await self.client.get_collections()
                collection_names = [c.name for c in collections_response.collections]

                if COLLECTION_NAME not in collection_names:
                    # 如果集合不存在，则创建它
                    await self.client.recreate_collection(
                        collection_name=COLLECTION_NAME,
                        vectors_config=models.VectorParams(
                            size=384,  # all-MiniLM-L6-v2的向量维度
                            distance=models.Distance.COSINE
                        ),
                    )
                    print(f"✓ Qdrant集合 '{COLLECTION_NAME}' 创建成功。")

                self.collection_initialized = True
                print("✓ Semantic Cache 初始化成功")
                return

            except Exception as e:
                print(f"Attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                else:
                    raise RuntimeError(f"Failed to initialize Semantic Cache after {retries} retries")

    async def get_cached_answer(self, text: str, threshold: float = 0.95) -> Optional[Dict]:
        """使用Qdrant查询语义缓存，包括音频文件信息"""
        if not self.collection_initialized:
            raise RuntimeError("SemanticCache has not been initialized. Call initialize() first.")
        try:
            print(f"Searching cache for: '{text}' with threshold {threshold}")
            model = self._get_embedding_model()
            query_vector = model.encode(text).tolist()
            search_result = await self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                limit=1,
                score_threshold=threshold,
            )
            if search_result:
                score = search_result[0].score
                payload = search_result[0].payload
                cached_question = payload.get('question', '')
                print(f"Cache hit with score {score:.3f} for question: '{cached_question}'")

                # 二次校验：对比当前问题与缓存问题的向量相似度，防止坏向量导致的误命中
                if cached_question:
                    import numpy as np
                    vec_current = np.array(query_vector)
                    vec_cached = np.array(model.encode(cached_question).tolist())
                    norm_current = np.linalg.norm(vec_current)
                    norm_cached = np.linalg.norm(vec_cached)
                    if norm_current > 0 and norm_cached > 0:
                        cross_score = float(np.dot(vec_current, vec_cached) / (norm_current * norm_cached))
                    else:
                        cross_score = 0.0
                    print(f"Cross-validation score: {cross_score:.3f} (threshold: {threshold})")
                    if cross_score < threshold:
                        print(f"Cache rejected: cross-validation failed ({cross_score:.3f} < {threshold}), skipping cache.")
                        return None

                print(f"Cache contains audio_url: {payload.get('audio_url')}, file_size: {payload.get('audio_file_size')}")
                if isinstance(payload.get("sources"), str):
                    payload["sources"] = json.loads(payload["sources"])
                # 确保返回的数据包含音频信息
                if "audio_url" not in payload:
                    payload["audio_url"] = None
                if "audio_file_size" not in payload:
                    payload["audio_file_size"] = 0
                return payload
            else:
                print(f"No cache hit found for: '{text}'")
        except Exception as e:
            print(f"Error querying semantic cache from Qdrant: {e}")
            return None
        return None

    async def set_cached_answer(self, text: str, answer: str, sources: List[Dict], audio_url: Optional[str] = None, audio_file_size: int = 0):
        """使用Qdrant设置语义缓存，包括音频文件信息"""
        if not self.collection_initialized:
            raise RuntimeError("SemanticCache has not been initialized. Call initialize() first.")
        try:
            # 使用uuid.uuid5从问题文本生成一个确定性的、格式正确的UUID
            point_id = str(uuid.uuid5(NAMESPACE_UUID, text))
            vector = self._get_embedding_model().encode(text).tolist()

            payload = {
                "question": text, 
                "answer": answer, 
                "sources": json.dumps(sources),
                "audio_url": audio_url,
                "audio_file_size": audio_file_size
            }

            await self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )
                ],
                wait=True,
            )
            print(f"Cached answer with audio info: audio_url={audio_url}, file_size={audio_file_size}")
        except Exception as e:
            print(f"Error setting semantic cache in Qdrant: {e}")


# 全局变量，稍后在应用生命周期中初始化
cache_service: Optional[SemanticCache] = None


def get_cache_service() -> SemanticCache:
    """依赖注入函数，确保服务已被初始化，并供其他模块安全调用"""
    if cache_service is None:
        raise RuntimeError("Cache service is not initialized.")
    return cache_service


async def init_cache_service():
    """
    全局初始化函数，创建实例并调用其包含重试逻辑的异步初始化方法。
    这个函数将在main.py的lifespan事件中被调用。
    """
    global cache_service
    if cache_service is None:
        if settings.DISABLE_SEMANTIC_CACHE:
            cache_service = NoOpSemanticCache()
        else:
            cache_service = SemanticCache()
        await cache_service.initialize()
