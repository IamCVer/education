// src/hooks/useSpeechService.ts
import { useState, useRef, useCallback } from 'react';

interface UseSpeechServiceOptions {
  endpoint?: string;
  onTranscriptUpdate?: (text: string) => void;
}

export const useSpeechService = (options: UseSpeechServiceOptions = {}) => {
  const { 
    endpoint = process.env.NEXT_PUBLIC_VOSK_SERVICE_URL || 'http://localhost:3002/transcribe',
    onTranscriptUpdate 
  } = options;

  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);

  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const mediaStream = useRef<MediaStream | null>(null);
  const chunks = useRef<Blob[]>([]);

  const start = useCallback(async () => {
    if (isRecording || isLoading) {
      console.log('[SpeechService] 无法开始录音:', { isRecording, isLoading });
      return;
    }

    setError(null);
    setTranscript('');
    console.log('[SpeechService] 开始录音...');

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000, // 尝试请求 16kHz 采样率
        } 
      });
      
      mediaStream.current = stream;
      console.log('[SpeechService] 麦克风授权成功');

      // 尝试使用 audio/wav，如果不支持则降级到 audio/webm
      let mimeType = 'audio/wav';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/webm';
        console.log('[SpeechService] 不支持 audio/wav，使用 audio/webm');
      }

      mediaRecorder.current = new MediaRecorder(stream, { mimeType });
      chunks.current = [];

      mediaRecorder.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.current.push(e.data);
          console.log('[SpeechService] 收到音频数据块:', e.data.size, 'bytes');
        }
      };

      mediaRecorder.current.onstop = async () => {
        console.log('[SpeechService] 录音停止，准备上传');
        const blob = new Blob(chunks.current, { type: mimeType });
        console.log('[SpeechService] 音频 Blob 大小:', blob.size, 'bytes');
        await upload(blob);
        
        // 停止所有音轨
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.current.onerror = (e: Event) => {
        console.error('[SpeechService] MediaRecorder 错误:', e);
        setError('录音过程出错');
        setIsRecording(false);
      };

      mediaRecorder.current.start();
      setIsRecording(true);
      console.log('[SpeechService] 录音已开始，等待语音输入...');
    } catch (e: any) {
      console.error('[SpeechService] 启动录音失败:', e);
      setError('麦克风授权失败或找不到设备');
    }
  }, [isRecording, isLoading]);

  const stop = useCallback(() => {
    if (!isRecording || !mediaRecorder.current) {
      console.log('[SpeechService] 没有正在进行的录音');
      return;
    }

    console.log('[SpeechService] 停止录音...');
    mediaRecorder.current.stop();
    setIsRecording(false);
  }, [isRecording]);

  const upload = async (blob: Blob) => {
    setIsLoading(true);
    setError(null);

    try {
      console.log('[SpeechService] 开始上传音频到:', endpoint);
      const formData = new FormData();
      formData.append('audio', blob, 'recording.webm');

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`服务器返回错误 ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log('[SpeechService] 识别结果:', data);
      
      const text = data.text ?? '';
      setTranscript(text);
      
      if (onTranscriptUpdate) {
        onTranscriptUpdate(text);
      }
    } catch (e: any) {
      console.error('[SpeechService] 上传或识别失败:', e);
      setError(`语音识别失败: ${e.message || String(e)}`);
    } finally {
      setIsLoading(false);
    }
  };

  return { 
    isRecording, 
    isLoading,
    transcript, 
    error, 
    start, 
    stop 
  };
};

