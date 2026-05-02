# Dockerfile (简化版 - 单阶段构建)
# 解决网络超时问题，提高构建成功率

FROM python:3.10-bookworm

# 设置UTF-8编码
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONUNBUFFERED=1

WORKDIR /code

# 使用清华大学镜像源加速apt安装
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt
COPY ./requirements.txt /code/requirements.txt

# 升级pip并配置国内镜像源
RUN pip install --no-cache-dir --upgrade pip

# 分批安装依赖，避免超时
# 第1批：小型基础包
RUN pip install --no-cache-dir --timeout 3600 \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    fastapi uvicorn[standard] websockets \
    pydantic pydantic-settings pydantic[email] \
    tortoise-orm==0.21.7 aiomysql neo4j \
    arq redis \
    passlib==1.7.4 bcrypt==3.2.2 python-jose[cryptography] python-multipart \
    httpx pyyaml==6.0.1 \
    "python-socketio>=5.11.0" "psutil>=5.9.0" \
    "oss2>=2.18.0" || \
    pip install --no-cache-dir --timeout 3600 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    fastapi uvicorn[standard] websockets \
    pydantic pydantic-settings pydantic[email] \
    tortoise-orm==0.21.7 aiomysql neo4j \
    arq redis \
    passlib==1.7.4 bcrypt==3.2.2 python-jose[cryptography] python-multipart \
    httpx pyyaml==6.0.1 \
    python-socketio>=5.11.0 psutil>=5.9.0 \
    oss2>=2.18.0

# 第2批：AI框架（较大）
RUN pip install --no-cache-dir --timeout 3600 \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    langchain==0.2.5 langchain-core==0.2.8 langgraph==0.1.1 \
    langchain-community==0.2.4 langchain-openai==0.1.8 \
    qdrant-client~=1.9.0 || \
    pip install --no-cache-dir --timeout 3600 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    langchain==0.2.5 langchain-core==0.2.8 langgraph==0.1.1 \
    langchain-community==0.2.4 langchain-openai==0.1.8 \
    qdrant-client~=1.9.0

# 第3批：数据处理和外部API依赖
RUN pip install --no-cache-dir --timeout 3600 \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    dashscope>=1.14.0 soundfile>=0.12.1 numpy>=1.24.0 \
    pandas>=2.0.0 pyarrow>=12.0.0 aiofiles pypdf python-docx python-pptx || \
    pip install --no-cache-dir --timeout 3600 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    dashscope>=1.14.0 soundfile>=0.12.1 numpy>=1.24.0 \
    pandas>=2.0.0 pyarrow>=12.0.0 aiofiles pypdf python-docx python-pptx

# 安装mattermostdriver
RUN pip install --no-cache-dir mattermostdriver

WORKDIR /code

# 复制应用代码
COPY ./app /code/app

# 复制 teacher 模块代码
COPY ./teacher /code/teacher

# 复制静态文件
COPY ./app/static /code/app/static

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# 默认命令（会被docker-compose覆盖）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
