// src/hooks/useVoskBrowser.ts
// 【B】STT: 使用浏览器 Web Speech API 进行语音识别
import { useState, useRef, useCallback, useEffect } from 'react';

interface UseVoskBrowserOptions {
  modelPath?: string;
  onTranscriptUpdate?: (text: string) => void;
}

export const useVoskBrowser = (options: UseVoskBrowserOptions = {}) => {
  const { 
    modelPath = '/models/vosk-model-small-cn-0.22.tar.gz',
    onTranscriptUpdate 
  } = options;

  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [modelLoaded, setModelLoaded] = useState(true); // Web Speech API 无需加载模型

  // ========== 【新实现】Web Speech API ==========
  const recognizerRef = useRef<any>(null);

  useEffect(() => {
    // 检查浏览器是否支持 Web Speech API
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      console.error('[WebSpeech] 浏览器不支持 Web Speech API');
      setError('浏览器不支持语音识别功能');
      setModelLoaded(false);
      return;
    }

    console.log('[WebSpeech] Web Speech API 可用');
    setModelLoaded(true);

    return () => {
      if (recognizerRef.current) {
        try {
          recognizerRef.current.abort();
        } catch (e) {
          console.error('清理识别器失败:', e);
        }
      }
    };
  }, []);

  const start = useCallback(async () => {
    if (!modelLoaded) {
      setError('浏览器不支持语音识别');
      return;
    }

    if (isRecording) {
      console.log('[WebSpeech] 已在录音中');
      return;
    }

    setError(null);
    setTranscript('');
    console.log('[WebSpeech] 开始录音...');

    try {
      const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognizer = new SR();
      recognizer.lang = 'zh-CN';
      recognizer.continuous = false;
      recognizer.interimResults = true;

      recognizer.onresult = (e: any) => {
        const result = e.results[e.results.length - 1];
        const text = result[0].transcript;
        console.log('[WebSpeech] 识别结果:', text, 'isFinal:', result.isFinal);
        
        setTranscript(text);
        if (onTranscriptUpdate) {
          onTranscriptUpdate(text);
        }
      };

      recognizer.onerror = (e: any) => {
        console.error('[WebSpeech] 识别错误:', e.error);
        setError(`语音识别错误: ${e.error}`);
        setIsRecording(false);
      };

      recognizer.onend = () => {
        console.log('[WebSpeech] 识别结束');
        setIsRecording(false);
      };

      recognizerRef.current = recognizer;
      recognizer.start();
      setIsRecording(true);
      console.log('[WebSpeech] 录音已开始');

    } catch (e: any) {
      console.error('[WebSpeech] 启动录音失败:', e);
      setError(`启动语音识别失败: ${e.message}`);
    }
  }, [modelLoaded, isRecording, onTranscriptUpdate]);

  const stop = useCallback(() => {
    if (!isRecording || !recognizerRef.current) {
      console.log('[WebSpeech] 没有正在进行的录音');
      return;
    }

    console.log('[WebSpeech] 停止录音...');
    try {
      recognizerRef.current.stop();
    } catch (err) {
      console.error('[WebSpeech] 停止录音失败:', err);
    }
    setIsRecording(false);
  }, [isRecording]);

  const reset = useCallback(() => {
    setTranscript('');
    setError(null);
  }, []);

  return { 
    isRecording, 
    isLoading,
    transcript, 
    error,
    modelLoaded,
    start, 
    stop,
    reset
  };
  // ========== 【新实现结束】==========

  // ========== 【旧代码：Vosk】已注释保留 ==========
  /*
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [modelLoaded, setModelLoaded] = useState(false);

  // const modelRef = useRef<any>(null);
  // const recognizerRef = useRef<any>(null);
  // const audioContextRef = useRef<AudioContext | null>(null);
  // const streamRef = useRef<MediaStream | null>(null);
  // const processorRef = useRef<ScriptProcessorNode | null>(null);
  // const updateTimerRef = useRef<NodeJS.Timeout | null>(null);
  // const lastUpdateTimeRef = useRef<number>(0);

  /*
  // 加载模型
  useEffect(() => {
    let mounted = true;

    const loadModel = async () => {
      try {
        console.log('[VoskBrowser] 开始加载模型:', modelPath);
        setIsLoading(true);
        
        // 动态导入 vosk-browser
        const { createModel } = await import('vosk-browser');
        
        // 加载模型
        const model = await createModel(modelPath);
        
        if (mounted) {
          modelRef.current = model;
          setModelLoaded(true);
          setIsLoading(false);
          console.log('[VoskBrowser] 模型加载成功');
        }
      } catch (e: any) {
        console.error('[VoskBrowser] 模型加载失败:', e);
        if (mounted) {
          setError(`模型加载失败: ${e.message}`);
          setIsLoading(false);
        }
      }
    };

    loadModel();

    return () => {
      mounted = false;
      
      // 清理定时器
      if (updateTimerRef.current) {
        clearTimeout(updateTimerRef.current);
        updateTimerRef.current = null;
      }
      
      // 清理资源
      if (recognizerRef.current) {
        try {
          recognizerRef.current.free();
        } catch (e) {
          console.error('清理识别器失败:', e);
        }
      }
      if (modelRef.current) {
        try {
          modelRef.current.terminate();
        } catch (e) {
          console.error('清理模型失败:', e);
        }
      }
    };
  }, [modelPath]);

  const start = useCallback(async () => {
    if (!modelLoaded || !modelRef.current) {
      setError('模型尚未加载完成');
      return;
    }

    if (isRecording) {
      console.log('[VoskBrowser] 已在录音中');
      return;
    }

    setError(null);
    // 清空之前的识别结果
    setTranscript('');
    console.log('[VoskBrowser] 开始录音...');

    try {
      // 获取麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });

      streamRef.current = stream;

      // 创建音频上下文，指定16kHz采样率（Vosk 推荐）
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 16000
      });
      audioContextRef.current = audioContext;

      const sampleRate = audioContext.sampleRate;
      console.log('[VoskBrowser] 音频采样率:', sampleRate);

      // 创建识别器（必须传入采样率）
      const recognizer = new modelRef.current.KaldiRecognizer(sampleRate);
      // 禁用详细词信息以提高识别速度（不需要时间戳等详细信息）
      recognizer.setWords(false);
      recognizerRef.current = recognizer;

      let partialText = '';

      // 监听识别结果
      recognizer.on("result", (message: any) => {
        console.log('[VoskBrowser] 收到result事件, 内容:', message);
        if (message.result && message.result.text) {
          console.log('[VoskBrowser] 最终结果:', message.result.text);
          setTranscript(message.result.text);
          if (onTranscriptUpdate) {
            onTranscriptUpdate(message.result.text);
          }
        } else {
          console.log('[VoskBrowser] result事件但无文本内容');
        }
      });

      recognizer.on("partialresult", (message: any) => {
        if (message.result && message.result.partial && message.result.partial !== partialText) {
          partialText = message.result.partial;
          console.log('[VoskBrowser] 部分结果:', partialText);
          
          // 使用节流优化：限制更新频率为每100ms一次，提高响应速度
          const now = Date.now();
          const timeSinceLastUpdate = now - lastUpdateTimeRef.current;
          
          if (timeSinceLastUpdate >= 100) {
            // 立即更新
            lastUpdateTimeRef.current = now;
            setTranscript(partialText);
            if (onTranscriptUpdate) {
              onTranscriptUpdate(partialText);
            }
          } else {
            // 延迟更新，但确保最后一次结果不会丢失
            if (updateTimerRef.current) {
              clearTimeout(updateTimerRef.current);
            }
            updateTimerRef.current = setTimeout(() => {
              lastUpdateTimeRef.current = Date.now();
              setTranscript(partialText);
              if (onTranscriptUpdate) {
                onTranscriptUpdate(partialText);
              }
            }, 100 - timeSinceLastUpdate);
          }
        }
      });

      // 处理音频流
      const source = audioContext.createMediaStreamSource(stream);
      // 使用最小缓冲区 (1024) 以获得最低延迟和最快响应
      // 1024 是推荐的最小值，更小可能导致音频处理不稳定
      const processor = audioContext.createScriptProcessor(1024, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        if (!recognizer) return;

        try {
          // vosk-browser 的 acceptWaveform 接受 AudioBuffer
          recognizer.acceptWaveform(e.inputBuffer);
        } catch (err) {
          console.error('[VoskBrowser] 处理音频错误:', err);
        }
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      setIsRecording(true);
      console.log('[VoskBrowser] 录音已开始');

    } catch (e: any) {
      console.error('[VoskBrowser] 启动录音失败:', e);
      setError(`麦克风授权失败: ${e.message}`);
    }
  }, [modelLoaded, isRecording, onTranscriptUpdate]);

  const stop = useCallback(() => {
    if (!isRecording) {
      console.log('[VoskBrowser] 没有正在进行的录音');
      return;
    }

    console.log('[VoskBrowser] 停止录音...');

    // 在断开音频前，先通知识别器结束输入
    if (recognizerRef.current && audioContextRef.current) {
      try {
        console.log('[VoskBrowser] 发送结束信号给识别器...');
        // 创建一个空的音频缓冲区来结束识别
        const emptyBuffer = audioContextRef.current.createBuffer(
          1, 
          audioContextRef.current.sampleRate / 10, // 0.1秒的空白
          audioContextRef.current.sampleRate
        );
        recognizerRef.current.acceptWaveform(emptyBuffer);
      } catch (err) {
        console.error('[VoskBrowser] 发送结束信号失败:', err);
      }
    }

    // 清理定时器
    if (updateTimerRef.current) {
      clearTimeout(updateTimerRef.current);
      updateTimerRef.current = null;
    }

    // 先断开音频处理，停止新的音频输入
    if (processorRef.current) {
      try {
        processorRef.current.disconnect();
        processorRef.current = null;
      } catch (err) {
        console.error('[VoskBrowser] 断开processor失败:', err);
      }
    }

    // 清理音频资源
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // 使用当前的部分结果作为最终结果
    // 因为 vosk-browser 可能不会在停止时自动触发 result 事件
    if (recognizerRef.current) {
      try {
        console.log('[VoskBrowser] 使用最后的部分结果作为最终结果');
        console.log('[VoskBrowser] 当前 transcript:', transcript);
        
        // transcript 状态已经通过 partialresult 事件更新了
        // 直接触发最终的回调
        if (transcript && onTranscriptUpdate) {
          onTranscriptUpdate(transcript);
        }
        
        // 延迟一点时间再清理识别器
        setTimeout(() => {
          if (recognizerRef.current) {
            try {
              recognizerRef.current.remove();
              recognizerRef.current = null;
            } catch (err) {
              console.error('[VoskBrowser] 移除识别器失败:', err);
            }
          }
        }, 100);
      } catch (err) {
        console.error('[VoskBrowser] 处理最终结果失败:', err);
      }
    }

    setIsRecording(false);
  }, [isRecording, transcript, onTranscriptUpdate]);

  // 重置 transcript 状态的函数
  const reset = useCallback(() => {
    setTranscript('');
    setError(null);
  }, []);

  return { 
    isRecording, 
    isLoading,
    transcript, 
    error,
    modelLoaded,
    start, 
    stop,
    reset
  };
  */
};
