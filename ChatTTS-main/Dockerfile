# # ChatTTS Docker 镜像
# FROM python:3.10-slim

# # Install system dependencies for audio processing
# # Use a reliable mirror for the "trixie" distribution and trust it to avoid signature errors
# RUN echo "deb [trusted=yes] http://tuna.tsinghua.edu.cn/debian/ trixie main" > /etc/apt/sources.list && \
#     echo "deb [trusted=yes] http://tuna.tsinghua.edu.cn/debian/ trixie-updates main" >> /etc/apt/sources.list && \
#     echo "deb [trusted=yes] http://tuna.tsinghua.edu.cn/debian-security trixie-security main" >> /etc/apt/sources.list && \
#     apt-get update && \
#     apt-get install -y libsndfile1 ffmpeg libavformat-dev libavcodec-dev libavutil-dev libswresample-dev && \
#     rm -rf /var/lib/apt/lists/*
FROM python:3.10-bookworm

RUN rm -f /etc/apt/sources.list.d/debian.sources && \
    echo "deb [trusted=yes] https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb [trusted=yes] https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb [trusted=yes] https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        libsndfile1 ffmpeg libavformat-dev libavcodec-dev libavutil-dev libswresample-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
# 设置工作目录
WORKDIR /app

# 设置pip环境变量
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1  
ENV PIP_TIMEOUT=300

# 升级pip并安装wheel
RUN pip install --upgrade pip setuptools wheel

# 复制requirements文件
COPY requirements.txt .

# 分步安装依赖，每个包单独安装以避免下载中断
RUN pip install --no-cache-dir numpy==1.24.0
RUN pip install --no-cache-dir tqdm
RUN pip install --no-cache-dir fastapi
RUN pip install --no-cache-dir "uvicorn[standard]"
RUN pip install --no-cache-dir IPython

# 安装 PyTorch CPU版本（使用官方PyTorch源）
RUN pip install --no-cache-dir --timeout 1200 --retries 10 \
    --index-url https://download.pytorch.org/whl/cpu \
    torch \
    torchaudio

# 安装其他依赖（使用官方PyPI源）
RUN pip install --no-cache-dir --timeout 600 --retries 5 \
    soundfile \
    numba \
    vector_quantize_pytorch \
    transformers \
    vocos \
    av \
    pydub \
    pybase16384 \
    huggingface_hub \
    torchcodec

# 复制ChatTTS源码
COPY ChatTTS/ ./ChatTTS/
COPY tools/ ./tools/
COPY chattts_api.py .
COPY init_models.py .
COPY voice_template/ ./voice_template/

# ChatTTS 运行时依赖 requests，但旧镜像缺失该包，单独放在后段以减少重建成本
RUN pip install --no-cache-dir requests

# 如果存在 .cache 目录，复制预下载的模型文件
# 使用 COPY --from 或者在构建时手动复制，这里注释掉避免构建失败
# COPY .cache /app/.cache

# 暴露端口
EXPOSE 9000

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV HF_ENDPOINT=https://hf-mirror.com
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV HF_HOME=/app/.cache/huggingface

# 创建缓存目录
RUN mkdir -p /app/.cache/huggingface

# 创建启动脚本
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "============================================"\n\
echo "ChatTTS 容器启动"\n\
echo "============================================"\n\
echo "HuggingFace 镜像: $HF_ENDPOINT"\n\
echo "缓存目录: $HF_HOME"\n\
echo "============================================"\n\
\n\
# 检查模型文件是否已存在\n\
if [ -d "/app/.cache/huggingface/hub/models--2Noise--ChatTTS/snapshots" ]; then\n\
    snapshots=$(find /app/.cache/huggingface/hub/models--2Noise--ChatTTS/snapshots -mindepth 1 -maxdepth 1 -type d | head -1)\n\
    if [ -n "$snapshots" ]; then\n\
        model_count=$(find "$snapshots" -type f \( -name "*.safetensors" -o -name "*.json" \) | wc -l)\n\
        if [ "$model_count" -gt 10 ]; then\n\
            echo "✓ 检测到本地模型文件，跳过下载"\n\
            echo "✓ 模型文件数: $model_count"\n\
        else\n\
            echo "⚠ 模型文件不完整，尝试补全..."\n\
            python init_models.py || echo "⚠ 模型下载失败，API启动时会自动下载"\n\
        fi\n\
    fi\n\
else\n\
    echo ""\n\
    echo "[步骤 1/2] 下载模型..."\n\
    if python init_models.py; then\n\
        echo "✓ 模型下载成功"\n\
    else\n\
        echo "✗ 模型下载失败"\n\
        echo "⚠ 警告: 模型未能预下载，API启动时会自动下载"\n\
        echo "⚠ 这可能导致首次请求响应较慢"\n\
    fi\n\
fi\n\
\n\
# 启动API服务\n\
echo ""\n\
echo "[步骤 2/2] 启动API服务..."\n\
echo "监听地址: 0.0.0.0:9000"\n\
echo "============================================"\n\
uvicorn chattts_api:app --host 0.0.0.0 --port 9000 --timeout-keep-alive 300' > /app/start.sh && \
    chmod +x /app/start.sh

# 启动脚本
CMD ["/bin/bash", "/app/start.sh"]

