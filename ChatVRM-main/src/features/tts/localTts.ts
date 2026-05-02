/**
 * 阿里云 CosyVoice TTS 集成（女声）
 * ChatVRM 专用 - 使用固定女声音色
 * 已从 ChatTTS 迁移至阿里云 CosyVoice API
 */

// 优先使用显式配置的后端地址，避免在 3001 上误打到 ChatVRM 自身。
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// ============== 【已停用】ChatTTS 配置 ==============
// const CHATTTS_API_URL = process.env.NEXT_PUBLIC_CHATTTS_API_URL || 'http://localhost:9000';
// ============== 【已停用】ChatTTS 配置 结束 ==============

export async function synthesizeLocalVoice(
  message: string,
  token: string
): Promise<{ audio: string }> {
  console.log('📤 调用阿里云 CosyVoice API（女声），文本长度:', message.length);
  
  try {
    // 调用 FastAPI 后端的 TTS API（阿里云 CosyVoice）
    const formData = new FormData();
    formData.append('text', message);
    formData.append('voice_type', 'female');  // 使用女声
    
    const response = await fetch(`${API_BASE_URL}/api/v1/tts/stream`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`CosyVoice API 生成失败: ${response.status} - ${errorText}`);
    }
    
    // 获取音频流并转为 Blob
    const audioBlob = await response.blob();
    console.log('📦 收到音频数据，大小:', audioBlob.size, 'bytes, 类型:', audioBlob.type);
    
    // 创建本地 URL
    const audioUrl = URL.createObjectURL(audioBlob);
    
    console.log('✅ 阿里云 CosyVoice 生成成功（女声），URL:', audioUrl);
    
    return { audio: audioUrl };
    
  } catch (error) {
    console.error('❌ 阿里云 CosyVoice API 调用失败:', error);
    throw error;
  }
}

// ============== 【已停用】ChatTTS 实现 ==============
// export async function synthesizeLocalVoice(
//   message: string,
//   token: string
// ): Promise<{ audio: string }> {
//   console.log('📤 调用 ChatTTS 服务（女声），文本长度:', message.length);
//   
//   try {
//     // 调用 ChatTTS API，使用女声
//     const response = await fetch(`${CHATTTS_API_URL}/generate_audio`, {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify({
//         text: message,
//         temperature: 0.3,
//         top_p: 0.7,
//         top_k: 20,
//         voice_type: 'female'  // 使用女声
//       })
//     });
//     
//     if (!response.ok) {
//       const errorText = await response.text();
//       throw new Error(`ChatTTS 生成失败: ${response.status} - ${errorText}`);
//     }
//     
//     // 获取音频流并转为 Blob
//     const audioBlob = await response.blob();
//     console.log('📦 收到音频数据，大小:', audioBlob.size, 'bytes, 类型:', audioBlob.type);
//     
//     // 创建本地 URL
//     const audioUrl = URL.createObjectURL(audioBlob);
//     
//     console.log('✅ ChatTTS 生成成功（女声），URL:', audioUrl);
//     
//     return { audio: audioUrl };
//     
//   } catch (error) {
//     console.error('❌ ChatTTS 生成失败:', error);
//     throw error;
//   }
// }
// ============== 【已停用】ChatTTS 实现 结束 ==============

