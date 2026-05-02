# app/api/v1/logs.py
"""
Docker 服务监控 API - 直接通过 Unix Socket 访问 Docker API
"""
import json
import socket
import urllib.parse
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query

from app.api.deps import get_admin_user
from app.models.user_model import User

router = APIRouter()

# 可用的服务列表
AVAILABLE_SERVICES = ["frontend", "backend", "chattts", "worker"]

# Docker socket 路径
DOCKER_SOCKET = "/var/run/docker.sock"


def docker_api_request(method: str, path: str) -> Dict[str, Any]:
    """
    通过 Unix Socket 发送 HTTP 请求到 Docker API
    """
    try:
        # 创建 Unix Socket 连接
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(DOCKER_SOCKET)
        
        # 构建 HTTP 请求
        request = f"{method} {path} HTTP/1.1\r\nHost: localhost\r\n\r\n"
        sock.sendall(request.encode())
        
        # 接收响应
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            # 简单判断是否接收完成
            if b"\r\n\r\n" in response and len(chunk) < 4096:
                break
        
        sock.close()
        
        # 解析响应
        response_str = response.decode('utf-8', errors='replace')
        parts = response_str.split('\r\n\r\n', 1)
        
        if len(parts) < 2:
            return {}
        
        # 尝试解析 JSON
        try:
            return json.loads(parts[1])
        except:
            return {"raw": parts[1]}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Docker API 请求失败: {str(e)}")


def get_container_logs(container_name: str, lines: int = 50) -> str:
    """
    获取容器日志
    """
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(5.0)  # 设置5秒超时
        sock.connect(DOCKER_SOCKET)
        
        # 构建请求路径
        path = f"/containers/{container_name}/logs?stdout=1&stderr=1&tail={lines}&timestamps=1"
        request = f"GET {path} HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n"
        sock.sendall(request.encode())
        
        # 接收响应（设置总大小限制）
        response = b""
        max_size = 1024 * 1024  # 1MB 限制
        while len(response) < max_size:
            try:
                chunk = sock.recv(8192)
                if not chunk:
                    break
                response += chunk
            except socket.timeout:
                break
        
        sock.close()
        
        # 解析响应
        response_str = response.decode('utf-8', errors='replace')
        parts = response_str.split('\r\n\r\n', 1)
        
        if len(parts) < 2:
            return ""
        
        # Docker 日志格式：每行前8字节是头信息
        logs_data = parts[1]
        
        # 清理日志数据（移除二进制头）
        lines_list = []
        i = 0
        while i < len(logs_data):
            # 跳过 8 字节头
            if i + 8 < len(logs_data):
                i += 8
            # 查找换行符
            end = logs_data.find('\n', i)
            if end == -1:
                line = logs_data[i:]
                if line.strip():
                    lines_list.append(line)
                break
            else:
                line = logs_data[i:end]
                if line.strip():
                    lines_list.append(line)
                i = end + 1
        
        return '\n'.join(lines_list[-lines:]) if lines_list else "暂无日志"
        
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="无法访问 Docker socket，请确保已挂载")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")


@router.get("/services")
async def get_services(current_user: User = Depends(get_admin_user)):
    """获取可用的服务列表"""
    return {"services": [
        {"name": service, "container": f"my_project_{service}"} 
        for service in AVAILABLE_SERVICES
    ]}


@router.get("/{service}")
async def get_service_logs(
    service: str,
    lines: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_admin_user)
):
    """获取指定服务的日志"""
    if service not in AVAILABLE_SERVICES:
        raise HTTPException(status_code=400, detail=f"无效的服务名称: {service}")
    
    try:
        container_name = f"my_project_{service}"
        logs = get_container_logs(container_name, lines)
        
        return {
            "logs": logs,
            "service": service,
            "container": container_name,
            "lines_count": len(logs.split('\n'))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")


@router.get("/{service}/status")
async def get_service_status(
    service: str,
    current_user: User = Depends(get_admin_user)
):
    """获取服务状态信息"""
    if service not in AVAILABLE_SERVICES:
        raise HTTPException(status_code=400, detail=f"无效的服务名称: {service}")
    
    try:
        container_name = f"my_project_{service}"
        
        # 获取容器信息
        container_info = docker_api_request("GET", f"/containers/{container_name}/json")
        
        if not container_info or "State" not in container_info:
            raise HTTPException(status_code=404, detail=f"容器 {container_name} 不存在")
        
        state = container_info.get("State", {})
        
        return {
            "service": service,
            "container": container_name,
            "status": state.get("Status", "unknown"),
            "running": state.get("Running", False),
            "paused": state.get("Paused", False),
            "restarting": state.get("Restarting", False),
            "pid": state.get("Pid", 0),
            "started_at": state.get("StartedAt", ""),
            "health": state.get("Health", {}).get("Status", "none")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")
