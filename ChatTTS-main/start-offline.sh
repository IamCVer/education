#!/bin/bash
# ChatTTS 离线模式快速启动脚本

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "ChatTTS 离线模式启动"
echo "=========================================="
echo ""

# 检查模型目录
MODEL_DIR="D:/code/education/models/huggingface_cache"
echo "检查模型目录: $MODEL_DIR"

if [ ! -d "$MODEL_DIR/hub/models--2Noise--ChatTTS" ]; then
    echo -e "${RED}✗ 模型目录不存在${NC}"
    echo "请确保模型文件已放置在: $MODEL_DIR"
    exit 1
fi

MODEL_COUNT=$(find "$MODEL_DIR" -type f \( -name "*.safetensors" -o -name "*.json" -o -name "*.yaml" \) 2>/dev/null | wc -l)
if [ "$MODEL_COUNT" -lt 14 ]; then
    echo -e "${RED}✗ 模型文件不完整（当前: $MODEL_COUNT, 需要: >=14）${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 模型文件完整（$MODEL_COUNT 个文件）${NC}"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker 已安装${NC}"
echo ""

# 检查 GPU
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ NVIDIA 驱动已安装${NC}"
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
    echo "  GPU: $GPU_NAME"
else
    echo -e "${YELLOW}⚠ 未检测到 nvidia-smi${NC}"
fi
echo ""

# 启动服务
echo "启动 ChatTTS 服务..."
cd "$(dirname "$0")"

if docker compose -f docker-compose.gpu.yml up -d; then
    echo -e "${GREEN}✓ 服务启动成功${NC}"
else
    echo -e "${RED}✗ 服务启动失败${NC}"
    exit 1
fi
echo ""

# 等待启动
echo "等待服务初始化（30秒）..."
sleep 30
echo ""

# 健康检查
echo "执行健康检查..."
if curl -s http://localhost:9000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 服务健康检查通过${NC}"
    echo ""
    curl -s http://localhost:9000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:9000/health
else
    echo -e "${YELLOW}⚠ 健康检查未通过，查看日志...${NC}"
    docker logs --tail 50 chattts-gpu
fi
echo ""

echo "=========================================="
echo -e "${GREEN}✓ 启动完成${NC}"
echo "=========================================="
echo ""
echo "API 地址: http://localhost:9000"
echo ""
echo "测试命令:"
echo "  curl -X POST http://localhost:9000/generate_audio \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"text\":\"你好\",\"voice_type\":\"male\"}' \\"
echo "    --output test.wav"
echo ""
echo "查看日志: docker logs -f chattts-gpu"
echo "停止服务: docker compose -f docker-compose.gpu.yml down"
echo ""

