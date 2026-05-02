#!/usr/bin/env python3
"""
ChatTTS模型预下载脚本
在启动API服务之前先下载模型
如果检测到离线模式，则仅验证本地模型
"""
import logging
import time
import os
import sys

# 检查是否为离线模式
OFFLINE_MODE = os.environ.get('TRANSFORMERS_OFFLINE', '0') == '1' or \
               os.environ.get('HF_HUB_OFFLINE', '0') == '1'

if not OFFLINE_MODE:
    from huggingface_hub import snapshot_download

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ChatTTS-Init")

# 配置
MAX_RETRIES = 3
RETRY_DELAY = 10  # 秒
TIMEOUT = 600  # 10分钟超时

logger.info("=" * 60)
if OFFLINE_MODE:
    logger.info("ChatTTS 模型验证程序（离线模式）")
else:
    logger.info("ChatTTS 模型下载程序")
logger.info("=" * 60)
if OFFLINE_MODE:
    logger.info("检测到离线模式，仅验证本地模型")
else:
    logger.info(f"仓库: 2Noise/ChatTTS")
    logger.info(f"最大重试次数: {MAX_RETRIES}")
    logger.info(f"超时时间: {TIMEOUT}秒")
logger.info("=" * 60)

# 检查是否已有本地模型
cache_dir = os.environ.get('HF_HOME', '/app/.cache/huggingface')

# HuggingFace 默认使用 hub/ 子目录
local_model_paths = [
    os.path.join(cache_dir, 'hub', 'models--2Noise--ChatTTS', 'snapshots'),
    os.path.join(cache_dir, 'models--2Noise--ChatTTS', 'snapshots')
]

for local_model_path in local_model_paths:
    if os.path.exists(local_model_path):
        snapshots = [d for d in os.listdir(local_model_path) if os.path.isdir(os.path.join(local_model_path, d))]
        if snapshots:
            snapshot_path = os.path.join(local_model_path, snapshots[0])
            # 检查是否有必要的模型文件
            model_files = []
            for root, dirs, files in os.walk(snapshot_path):
                model_files.extend([f for f in files if f.endswith(('.safetensors', '.json', '.yaml'))])
            
            if len(model_files) >= 14:  # 应该有14个文件
                logger.info("=" * 60)
                logger.info("✓ 检测到本地已下载的模型！")
                logger.info(f"✓ 位置: {snapshot_path}")
                logger.info(f"✓ 文件数量: {len(model_files)}")
                if OFFLINE_MODE:
                    logger.info("✓ 离线模式：本地模型验证通过")
                else:
                    logger.info("✓ 跳过下载，直接使用本地模型")
                logger.info("=" * 60)
                exit(0)

# 离线模式下，如果模型不存在则报错退出
if OFFLINE_MODE:
    logger.error("=" * 60)
    logger.error("✗ 离线模式下未找到本地模型！")
    logger.error("=" * 60)
    logger.error("请确保：")
    logger.error("1. 模型文件已正确放置在: " + cache_dir)
    logger.error("2. 目录结构: hub/models--2Noise--ChatTTS/snapshots/<hash>/")
    logger.error("3. 包含至少 14 个 .safetensors, .json, .yaml 文件")
    logger.error("4. Docker 卷挂载路径正确")
    logger.error("=" * 60)
    sys.exit(1)

# 在线模式：尝试下载模型
logger.info("\n在线模式：开始下载模型...")
for attempt in range(1, MAX_RETRIES + 1):
    try:
        logger.info(f"\n[尝试 {attempt}/{MAX_RETRIES}] 开始下载模型...")
        logger.info("模型较大（约2GB），请耐心等待...")
        
        download_path = snapshot_download(
            repo_id="2Noise/ChatTTS",
            allow_patterns=["*.yaml", "*.json", "*.safetensors"],
            resume_download=True,  # 支持断点续传
            max_workers=4,  # 并发下载
        )
        
        logger.info("=" * 60)
        logger.info(f"✓ 模型下载成功！")
        logger.info(f"✓ 存储路径: {download_path}")
        logger.info("=" * 60)
        
        # 验证文件
        if os.path.exists(download_path):
            files = os.listdir(download_path)
            logger.info(f"✓ 已下载 {len(files)} 个文件")
            logger.info("模型初始化完成！")
            break
        else:
            raise Exception("下载路径不存在")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"✗ 第 {attempt} 次尝试失败")
        logger.error(f"✗ 错误信息: {error_msg}")
        
        if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            logger.warning("⚠ 网络超时，这通常是因为:")
            logger.warning("  1. HuggingFace 服务器响应慢")
            logger.warning("  2. 网络连接不稳定")
            logger.warning("  3. 防火墙/代理问题")
        
        if attempt < MAX_RETRIES:
            logger.info(f"⏳ {RETRY_DELAY}秒后重试...")
            time.sleep(RETRY_DELAY)
        else:
            logger.error("=" * 60)
            logger.error("✗ 所有下载尝试均失败！")
            logger.error("=" * 60)
            logger.error("建议:")
            logger.error("1. 检查网络连接")
            logger.error("2. 配置 HuggingFace 镜像源")
            logger.error("3. 手动下载模型到 ~/.cache/huggingface/hub/")
            logger.error("4. 使用代理: export HF_ENDPOINT=https://hf-mirror.com")
            logger.error("=" * 60)
            raise Exception(f"模型下载失败，已重试{MAX_RETRIES}次")

