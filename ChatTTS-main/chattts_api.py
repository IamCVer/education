import io
import os
import sys
import logging
from pathlib import Path
import re

# === 强制离线模式（必须在导入其他库之前设置）===
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_UPDATE_DOWNLOAD_COUNTS'] = 'false'

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import numpy as np
import soundfile as sf
import torchaudio

# 添加当前目录到系统路径
now_dir = os.getcwd()
sys.path.append(now_dir)

import ChatTTS

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ChatTTS-API")

app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境建议指定具体域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# 🆕 从环境变量读取模型路径
MODEL_PATH = Path(os.getenv("MODEL_PATH", "./models"))
if not MODEL_PATH.is_absolute():
    MODEL_PATH = Path(__file__).parent.parent / MODEL_PATH
MODEL_PATH = MODEL_PATH.resolve()

# 🆕 设置HuggingFace缓存目录
HF_CACHE = MODEL_PATH / "huggingface_cache"
os.environ["HF_HOME"] = str(HF_CACHE)
HF_CACHE.mkdir(parents=True, exist_ok=True)

logger.info(f"📁 模型路径: {MODEL_PATH}")
logger.info(f"📁 HuggingFace缓存: {HF_CACHE}")

# 全局ChatTTS实例和设备信息
chat = None
device_info = {
    "device": "cpu",
    "device_name": "CPU",
    "has_gpu": False
}

# 预设的 speaker embeddings
preset_speakers = {}
MALE_VOICE_ID = 4  # Chat页面使用男声（索引从0开始）
FEMALE_VOICE_ID = 13  # ChatVRM 使用女声

# +++ 新增：加载固定音色的 embedding +++

def _load_embedding(path: Path):
    """从给定路径加载 speaker embedding（支持 .pt 和 .npy 格式）；失败则返回 None"""
    try:
        if not path.exists():
            logger.warning(f"未找到 speaker embedding 文件: {path}")
            return None

        emb: torch.Tensor | None = None
        
        # 根据文件扩展名选择加载方式
        if path.suffix == '.npy':
            # 直接加载 .npy 文件（允许 pickle）
            logger.info(f"加载 .npy 格式文件: {path.name}")
            npy_data = np.load(path, allow_pickle=True)
            emb = torch.from_numpy(npy_data).float()
            logger.info(f"✓ 已从 .npy 加载 speaker embedding: {path.name}，shape: {tuple(emb.shape)}")
            
        elif path.suffix in ['.pt', '.pth']:
            # 加载 PyTorch 格式
            logger.info(f"加载 .pt 格式文件: {path.name}")
            obj = torch.load(path, map_location="cpu")

            # 某些文件保存为 dict 结构，需要提取真正的 embedding
            if isinstance(obj, torch.Tensor):
                emb = obj
            elif isinstance(obj, dict):
                # 常见字段名
                for key in ("speaker_embedding", "spk_emb", "embedding", "emb", "spk"):
                    if key in obj and isinstance(obj[key], torch.Tensor):
                        emb = obj[key]
                        break
                # 如果仍未找到，则尝试抓取第一个张量值
                if emb is None:
                    for v in obj.values():
                        if isinstance(v, torch.Tensor):
                            emb = v
                            break
            
            if emb is not None:
                logger.info(f"✓ 已从 .pt 加载 speaker embedding: {path.name}，shape: {tuple(emb.shape)}")
        else:
            logger.error(f"不支持的文件格式: {path.suffix}，仅支持 .npy, .pt, .pth")
            return None

        if emb is None:
            logger.error(f"在 {path.name} 中未找到有效的 speaker embedding")
            return None

        # 部分文件可能包含批维度，这里统一 squeeze 以免后续报 shape 错误
        emb = emb.squeeze()

        return emb

    except Exception as exc:
        logger.error(f"加载 speaker embedding 失败: {path} - {exc}")
        return None

# 🆕 使用models文件夹中的voice_template目录
VOICE_TEMPLATE_DIR = MODEL_PATH / "tts_voices"
VOICE_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

if not VOICE_TEMPLATE_DIR.exists():
    logger.warning(f"未找到 voice_template 目录: {VOICE_TEMPLATE_DIR}，已创建")
    VOICE_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

# 固定音色文件路径（支持 .npy 和 .pt 格式，优先使用 .npy）
MALE_VOICE_PATH = VOICE_TEMPLATE_DIR / "male_voice1.npy"
if not MALE_VOICE_PATH.exists():
    MALE_VOICE_PATH = VOICE_TEMPLATE_DIR / "speaker_04.pt"

FEMALE_VOICE_PATH = VOICE_TEMPLATE_DIR / "female_voice1.npy"
if not FEMALE_VOICE_PATH.exists():
    FEMALE_VOICE_PATH = VOICE_TEMPLATE_DIR / "speaker_13.pt"
# +++ 新增结束 +++


def detect_device():
    """检测可用的计算设备"""
    global device_info
    
    # 检测 CUDA (NVIDIA GPU)
    if torch.cuda.is_available():
        device_info["has_gpu"] = True
        device_info["device"] = "cuda"
        device_info["device_name"] = torch.cuda.get_device_name(0)
        logger.info(f"✓ 检测到 NVIDIA GPU: {device_info['device_name']}")
        logger.info(f"  CUDA 版本: {torch.version.cuda}")
        logger.info(f"  可用显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        return torch.device("cuda")
    
    # 检测 MPS (Apple Silicon)
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device_info["has_gpu"] = True
        device_info["device"] = "mps"
        device_info["device_name"] = "Apple Silicon (MPS)"
        logger.info(f"✓ 检测到 Apple Silicon GPU (MPS)")
        return torch.device("mps")
    
    # 使用 CPU
    else:
        device_info["has_gpu"] = False
        device_info["device"] = "cpu"
        device_info["device_name"] = "CPU"
        logger.warning("⚠ 未检测到 GPU，将使用 CPU 进行计算")
        logger.warning("  提示: CPU 模式下语音生成速度较慢")
        return torch.device("cpu")


@app.on_event("startup")
async def startup_event():
    global chat, preset_speakers
    
    logger.info("正在初始化ChatTTS...")
    
    # 检测设备
    device = detect_device()
    
    # 初始化 ChatTTS
    chat = ChatTTS.Chat(logger)
    
    # 加载模型到指定设备（强制使用本地文件，禁用网络检查）
    logger.info("使用离线模式加载模型（禁用网络检查）...")
    try:
        # 设置为 huggingface 模式会自动从 HF_HOME 读取本地模型
        if chat.load(source="huggingface", device=device, force_redownload=False):
            logger.info(f"✓ ChatTTS模型加载成功 (设备: {device_info['device_name']})")
        else:
            logger.error("✗ ChatTTS模型加载失败")
            logger.error("请检查模型文件是否存在于: /app/.cache/huggingface/hub/models--2Noise--ChatTTS/")
            sys.exit(1)
    except Exception as e:
        logger.error(f"✗ 模型加载异常: {e}")
        logger.error("提示: 确保已挂载包含模型文件的目录")
        sys.exit(1)
    
    # 生成预设的 speaker embeddings
    logger.info("正在生成预设的 speaker embeddings...")
    torch.manual_seed(42)  # 设置随机种子以确保可复现
    for i in range(20):
        # chat.sample_random_speaker() 返回的是字符串格式，保持原样
        preset_speakers[i] = chat.sample_random_speaker()
        # 调试：检查第一个 speaker 的类型
        if i == 0:
            logger.info(f"调试: preset_speakers[0] 类型: {type(preset_speakers[0])}")

    # +++ 新增：加载固定男声和女声音色 +++
    male_voice = _load_embedding(MALE_VOICE_PATH)
    female_voice = _load_embedding(FEMALE_VOICE_PATH)
    
    if male_voice is not None:
        male_voice = male_voice.to(device)
        preset_speakers[MALE_VOICE_ID] = male_voice
        logger.info(f"✓ 已加载固定男声音色: {MALE_VOICE_PATH.name}")
        logger.info(f"  设备: {male_voice.device}, shape: {male_voice.shape}, dtype: {male_voice.dtype}")
    else:
        logger.warning(f"⚠️ 男声音色文件加载失败: {MALE_VOICE_PATH}，使用随机音色")
    
    if female_voice is not None:
        female_voice = female_voice.to(device)
        preset_speakers[FEMALE_VOICE_ID] = female_voice
        logger.info(f"✓ 已加载固定女声音色: {FEMALE_VOICE_PATH.name}")
        logger.info(f"  设备: {female_voice.device}, shape: {female_voice.shape}, dtype: {female_voice.dtype}")
    else:
        logger.warning(f"⚠️ 女声音色文件加载失败: {FEMALE_VOICE_PATH}，使用随机音色")
    # +++ 新增结束 +++

    logger.info(f"✓ 已生成 {len(preset_speakers)} 个预设 speaker embeddings")


class TTSRequest(BaseModel):
    text: str
    temperature: float = 0.3
    top_p: float = 0.7
    top_k: int = 20
    voice_type: str = "male"  # 音色类型: "male"（男声）或 "female"（女声）


def preprocess_text(text: str) -> str:
    """对输入文本做最小必要清理。

    1. **不过度截断**：保留完整语句长度，避免生成残缺；
    2. **保留分句标点**：保留中文句号、逗号等，让 ChatTTS 自带的 `split_text` 能正确分句；
    3. **仅剔除控制字符和非常规不可打印符号**。
    """

    # 去除不可打印控制字符（换行符除外，留给 split_text 使用）
    text = re.sub(r"[\x00-\x08\x0B-\x1F\x7F]", "", text)

    # 可选：限制极端超长文本，防止 CPU 模式卡死（1-2 KB 足够）
    max_length = 1024
    if len(text) > max_length:
        text = text[:max_length]

    return text.strip()


@app.post("/generate_audio")
async def generate_audio(request: TTSRequest):
    """
    生成语音API端点
    接收文本，返回WAV格式的音频数据
    """
    try:
        logger.info(f"收到TTS请求，原始文本: {request.text[:50]}...")
        logger.info(f"🔍 请求参数 - voice_type: {request.voice_type}")
        
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="文本不能为空")
        
        # 预处理文本
        processed_text = preprocess_text(request.text)
        logger.info(f"处理后文本长度: {len(processed_text)} 字符")
        logger.info(f"处理后文本: {processed_text[:100]}..." if len(processed_text) > 100 else f"处理后文本: {processed_text}")
        
        if not processed_text:
            raise HTTPException(status_code=400, detail="处理后文本为空")
        
        # 设置推理参数
        params_infer_code = ChatTTS.Chat.InferCodeParams(
            temperature=request.temperature,
            top_P=request.top_p,
            top_K=request.top_k,
        )
        
        # 根据 voice_type 选择音色
        if request.voice_type == "female":
            spk = preset_speakers[FEMALE_VOICE_ID]
            logger.info(f"✓ 使用女声音色（ID={FEMALE_VOICE_ID}）")
        else:
            # 默认使用男声
            spk = preset_speakers[MALE_VOICE_ID]
            logger.info(f"✓ 使用男声音色（ID={MALE_VOICE_ID}）")
        
        # 统一处理 speaker embedding 格式
        # ChatTTS 的 sample_random_speaker() 返回字符串，但某些操作需要 Tensor
        # 如果是字符串格式，需要先转换为 Tensor
        if isinstance(spk, str):
            # 字符串格式的 speaker，ChatTTS 内部会处理
            logger.info(f"🔍 调试信息 - Speaker embedding (String) 类型: {type(spk)}, 长度: {len(spk)}")
        elif isinstance(spk, torch.Tensor):
            logger.info(f"🔍 调试信息 - Speaker embedding (Tensor) shape: {spk.shape}, device: {spk.device}, dtype: {spk.dtype}")
            logger.info(f"🔍 调试信息 - Speaker embedding 前5个值: {spk[:5].tolist()}")
        
        params_infer_code.spk_emb = spk
        
        # 根据设备类型选择不同的参数配置
        if device_info["has_gpu"]:
            # GPU 模式：可以使用完整功能
            logger.info("使用 GPU 模式生成语音（完整功能）")
            params_refine_text = ChatTTS.Chat.RefineTextParams(
                prompt='[oral_2][laugh_0][break_4]'
            )
            wavs = chat.infer(
                text=processed_text,  # 直接传字符串
                skip_refine_text=False,  # GPU 模式下启用文本优化
                params_refine_text=params_refine_text,
                params_infer_code=params_infer_code,
                use_decoder=True,
                do_text_normalization=True,  # GPU 模式下启用文本归一化
                split_text=True,  # 不自动分割
            )
        else:
            # CPU 模式：使用简化配置避免 narrow 错误
            logger.info("使用 CPU 模式生成语音（简化配置）")
            
            # CPU 模式下也需要传递 RefineTextParams 以确保 speaker embedding 生效
            params_refine_text = ChatTTS.Chat.RefineTextParams(
                prompt='[oral_2][laugh_0][break_4]'
            )
            
            wavs = chat.infer(
                text=processed_text,  # 直接传字符串，让ChatTTS自动处理
                skip_refine_text=False,  # 改为 False 以确保 speaker embedding 生效
                params_refine_text=params_refine_text,
                params_infer_code=params_infer_code,
                use_decoder=True,
                do_text_normalization=False,  # CPU 模式下关闭文本归一化
                split_text=False,  # 不自动分割文本
            )
        
        if not wavs or len(wavs) == 0:
            raise HTTPException(status_code=500, detail="语音生成失败")
        
        # 获取第一个音频
        audio_data = wavs[0]
        
        # 创建内存缓冲区
        buffer = io.BytesIO()
        
        # 将音频写入内存缓冲区（24000Hz 是 ChatTTS 默认采样率）
        # 直接使用 soundfile 写入，以避免 torchaudio 在某些 CPU 构建中缺少 "soundfile" 后端导致的崩溃
        sf.write(buffer, audio_data, 24000, format="WAV", subtype="PCM_16")
        # 写入后将指针重置到起始位置，供后续读取
        buffer.seek(0)

        # 读取字节数据以返回
        audio_bytes = buffer.read()
        
        logger.info(f"语音生成成功，音频大小: {len(audio_bytes)} 字节")
        
        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=speech.wav"
            }
        )
        
    except HTTPException as e:
        # Re-raise HTTPException directly to preserve status code and details
        raise e
    except Exception as e:
        logger.error(f"语音生成错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"语音生成错误: {str(e)}")


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "model_loaded": chat is not None,
        "device": device_info["device"],
        "device_name": device_info["device_name"],
        "has_gpu": device_info["has_gpu"]
    }


@app.get("/speakers")
async def list_speakers():
    """列出可用的音色"""
    return {
        "available_voices": ["male", "female"],
        "male_voice_file": "male_voice1.npy",
        "female_voice_file": "female_voice1.npy",
        "note": "使用 voice_type 参数指定音色: 'male'（男声）或 'female'（女声）"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)

