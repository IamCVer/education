FROM python:3.10

# 使用阿里云镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|security.debian.org/debian-security|mirrors.aliyun.com/debian-security|g' /etc/apt/sources.list.d/debian.sources

# 安装 ffmpeg(pydub 依赖),添加重试和超时设置
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    -o Acquire::Retries=3 \
    -o Acquire::http::Timeout=30 \
    ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
COPY app/ ./app
COPY model/ ./model

ENV PYTHONUNBUFFERED=1
EXPOSE 3002
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "3002"]

