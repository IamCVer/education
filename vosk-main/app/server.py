from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
import json
import io
import os
import numpy as np
import tempfile

MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "/app/model/vosk-model-small-cn-0.22")
SAMPLE_RATE = 16000

print("Loading model...")
model = Model(MODEL_PATH)
print("Model loaded.")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 生产环境请改成前端域名
    allow_methods=["*"],
    allow_headers=["*"],
)

class Result(BaseModel):
    text: str

@app.post("/transcribe", response_model=Result)
async def transcribe(audio: UploadFile = File(...)):
    try:
        # 读取上传的音频文件
        audio_data = await audio.read()
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        try:
            # 使用 pydub 加载音频（支持多种格式）
            audio_segment = AudioSegment.from_file(temp_path)
            
            # 转换为 16kHz 单声道
            audio_segment = audio_segment.set_frame_rate(SAMPLE_RATE).set_channels(1)
            
            # 转换为 PCM 数据
            samples = np.array(audio_segment.get_array_of_samples(), dtype=np.int16)
            pcm_data = samples.tobytes()
            
            print(f"Audio info: duration={len(audio_segment)}ms, samples={len(samples)}, bytes={len(pcm_data)}")
            
            # 使用 Vosk 识别
            rec = KaldiRecognizer(model, SAMPLE_RATE)
            rec.SetWords(True)
            rec.SetMaxAlternatives(5)  # 获取多个候选结果
            rec.SetPartialWords(True)  # 启用部分识别
            
            # 分块处理音频数据
            chunk_size = 4000
            partial_results = []
            for i in range(0, len(pcm_data), chunk_size):
                chunk = pcm_data[i:i + chunk_size]
                if rec.AcceptWaveform(chunk):
                    result = json.loads(rec.Result())
                    if result.get("text"):
                        partial_results.append(result.get("text"))
                        print(f"Partial result: {result.get('text')}")
            
            # 获取最终结果
            final_result = json.loads(rec.FinalResult())
            print(f"Final result JSON: {final_result}")
            
            # 尝试从多个字段获取文本
            text = final_result.get("text", "")
            
            # 如果主结果为空，尝试从备选结果获取
            if not text and "alternatives" in final_result:
                alternatives = final_result["alternatives"]
                if alternatives and len(alternatives) > 0:
                    text = alternatives[0].get("text", "")
                    print(f"Using alternative: '{text}'")
            
            # 如果还是空，使用部分结果
            if not text and partial_results:
                text = " ".join(partial_results)
                print(f"Using partial results: '{text}'")
            
            print(f"Recognition result: '{text}'")
            return {"text": text}
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    except Exception as e:
        print(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

