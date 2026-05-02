# Vosk 语音识别服务

基于 Vosk 的中文语音识别 Docker 服务。

## 前置条件

1. 安装 Docker
2. 下载 Vosk 中文模型并解压到 `model/` 目录
   - 模型下载: https://alphacephei.com/vosk/models
   - 推荐: `vosk-model-small-cn-0.22`

## 目录结构

```
vosk-main/
├── model/                    # 放置解压后的模型文件夹
│   └── vosk-model-small-cn-0.22/
├── app/
│   ├── server.py            # FastAPI 应用
│   └── requirements.txt     # Python 依赖
├── Dockerfile
└── README.md
```

## 构建和运行

### 1. 准备模型文件

将下载的模型解压到 `model/` 目录下，确保结构如下：
```
model/
└── vosk-model-small-cn-0.22/
    ├── am/
    ├── graph/
    ├── ivector/
    └── conf/
```

### 2. 构建 Docker 镜像

```powershell
cd D:\code\education\vosk-main
docker build -t vosk-cn-service .
```

### 3. 运行容器

```powershell
docker run -d -p 3002:3002 --name vosk-service vosk-cn-service
```

### 4. 测试服务

访问 http://localhost:3002/docs 查看 API 文档

或使用 curl 测试：
```powershell
curl http://localhost:3002/health
```

## API 接口

### POST /transcribe

上传音频文件进行语音识别

- **参数**: `audio` (文件)
- **返回**: `{"text": "识别结果"}`
- **要求**: 音频采样率 16000 Hz

### GET /health

健康检查接口

- **返回**: `{"status": "ok"}`

## 管理容器

```powershell
# 查看日志
docker logs vosk-service

# 停止容器
docker stop vosk-service

# 启动容器
docker start vosk-service

# 删除容器
docker rm -f vosk-service

# 删除镜像
docker rmi vosk-cn-service
```

## 注意事项

1. 首次构建较慢，需要下载依赖和拷贝模型文件
2. 模型文件较大，确保有足够磁盘空间
3. 生产环境请修改 CORS 配置，不要使用 `allow_origins=["*"]`
4. 高并发场景可使用 gunicorn 多进程或 Kubernetes 扩容

