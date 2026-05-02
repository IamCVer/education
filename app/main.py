# app/main.py
"""
[职责] FastAPI应用的唯一主入口，负责组装路由和管理应用生命周期。
"""
import asyncio
import os
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, Query, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from tortoise import Tortoise
import socketio

from app.api.v1 import auth, qa, admin, graph_data
from app.api.v1 import stats, logs, datasets, notifications, groups  # 新增路由
from app.api.v1 import videos, courses  # 视频教学功能路由
from app.api.v1 import generate  # 互动内容生成路由
from teacher.backend.router import router as teacher_agent_router
from app.api.deps import get_user_from_token
from app.models.user_model import User
from app.ws_manager.connection_manager import manager
from app.db.tortoise_config import TORTOISE_ORM_CONFIG
from app.pubsub import redis_pubsub  # 导入重构后的pubsub模块
from app.services.caching_service import init_cache_service
from app.db.redis_client import init_redis_pool, close_redis_pool  # 导入Redis生命周期函数

# 创建 Socket.IO 服务器
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=False,
    engineio_logger=False
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI应用的生命周期管理器。
    """
    # --- 应用启动时 ---
    print("Application starting up...")
    await Tortoise.init(config=TORTOISE_ORM_CONFIG)
    await Tortoise.generate_schemas()
    print("Tortoise-ORM started and schemas generated.")
    await init_cache_service()
    await init_redis_pool()  # 初始化中央Redis客户端

    # 启动健壮的Redis订阅者
    subscriber_task = asyncio.create_task(
        redis_pubsub.robust_subscriber(redis_pubsub.message_handler)
    )
    
    # 启动 GPU 监控后台任务
    from app.api.v1.stats import collect_gpu_metrics, refresh_entities_ranking, refresh_community_tree, set_sio
    
    # 注入 Socket.IO 实例
    set_sio(sio)
    
    gpu_task = asyncio.create_task(collect_gpu_metrics())
    
    # 初始化统计数据
    await refresh_entities_ranking()
    await refresh_community_tree()
    
    print("Application startup complete.")
    yield
    # --- 应用关闭时 ---
    print("Application shutting down...")
    subscriber_task.cancel()
    gpu_task.cancel()
    await Tortoise.close_connections()
    await close_redis_pool()  # 关闭中央Redis客户端
    print("Tortoise-ORM and Redis connections closed.")
    try:
        await subscriber_task
    except asyncio.CancelledError:
        print("Subscriber task successfully cancelled.")
    try:
        await gpu_task
    except asyncio.CancelledError:
        print("GPU monitoring task successfully cancelled.")


app = FastAPI(
    title="智能学业知识问答及职业发展辅助系统",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# 挂载 Socket.IO
socket_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path='socket.io')

# Socket.IO 事件处理
@sio.event
async def connect(sid, environ, auth):
    print(f"Socket.IO client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Socket.IO client disconnected: {sid}")



@app.websocket("/api/v1/ws/qa")
async def websocket_endpoint(
        websocket: WebSocket,
        token: Annotated[str | None, Query()] = None
):
    user = await get_user_from_token(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(user.id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user.id)
    except Exception as e:
        print(f"An error occurred for client #{user.id}: {e}")
    finally:
        manager.disconnect(user.id)
        print(f"Connection for client #{user.id} closed and cleaned up.")


app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(qa.router, prefix="/api/v1", tags=["Q&A"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])
app.include_router(groups.router, prefix="/api/v1", tags=["Groups"])  # 群聊路由
app.include_router(videos.router, prefix="/api/v1/videos", tags=["Videos"])  # 视频管理路由
app.include_router(courses.router, prefix="/api/v1/courses", tags=["Courses"])  # 课程管理路由
app.include_router(generate.router, prefix="/api/v1/generate", tags=["Generate"])  # 互动内容生成路由
app.include_router(teacher_agent_router, prefix="/api/v1/teacher-agent", tags=["Teacher Agent"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(graph_data.router, prefix="/api/v1", tags=["Graph Data"])
app.include_router(stats.router, prefix="/api/v1/stats", tags=["Statistics"])
app.include_router(logs.router, prefix="/api/v1/logs", tags=["Logs"])
app.include_router(datasets.router, prefix="/api/v1/admin", tags=["Datasets"])


@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/pages/auth/login.html")


# 确保必要的目录存在
vue_assets_dir = "/code/app/static/vue_app/dist/assets"
media_dir = "/code/media"
os.makedirs(vue_assets_dir, exist_ok=True)
os.makedirs(media_dir, exist_ok=True)

# Vue应用静态文件（优先挂载，仅当目录非空时挂载）
if os.path.isdir(vue_assets_dir) and os.listdir(vue_assets_dir):
    app.mount("/vue_assets", StaticFiles(directory=vue_assets_dir), name="vue_assets")

# 旧的静态文件
app.mount("/assets", StaticFiles(directory="/code/app/static/templates/assets"), name="assets")
app.mount("/pages", StaticFiles(directory="/code/app/static/templates/pages", html=True), name="pages")
app.mount("/media", StaticFiles(directory=media_dir), name="media")  # 提供音频文件访问
app.mount("/static", StaticFiles(directory="/code/app/static"), name="static")

# Vue SPA catch-all路由（必须在最后）
# 必须接受所有方法，否则会对API路由的POST/PUT等请求返回405
@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"], include_in_schema=False)
async def serve_vue_spa(request: Request, full_path: str):
    from fastapi import HTTPException
    # API路径不由此路由处理
    if full_path.startswith(("api/", "socket.io/", "assets/", "vue_assets/", "media/", "pages/", "static/")):
        raise HTTPException(status_code=404, detail="Not found")
    # 非API路径返回Vue SPA（仅GET有意义，其他方法直接404）
    if request.method != "GET":
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse("/code/app/static/vue_app/dist/index.html")

# 导出 socket_app 作为 ASGI 应用
app = socket_app
