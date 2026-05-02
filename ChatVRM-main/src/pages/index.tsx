import { useCallback, useContext, useEffect, useState } from "react";
import VrmViewer from "@/components/vrmViewer";
import { ViewerContext } from "@/features/vrmViewer/viewerContext";
import {
  Message,
  textsToScreenplay,
  Screenplay,
} from "@/features/messages/messages";
import { speakCharacter } from "@/features/messages/speakCharacter";
import { MessageInputContainer } from "@/components/messageInputContainer";
import { SYSTEM_PROMPT } from "@/features/constants/systemPromptConstants";
import { KoeiroParam, DEFAULT_KOEIRO_PARAM } from "@/features/constants/koeiroParam";
import { getChatResponseStream } from "@/features/chat/openAiChat";
import { getQwenChatResponseStream, getAuthToken, validateToken } from "@/features/chat/fastApiChat";
// import { M_PLUS_2, Montserrat } from "next/font/google";
import { Introduction } from "@/components/introduction";
import { Menu } from "@/components/menu";
// import { GitHubLink } from "@/components/githubLink";
import { Meta } from "@/components/meta";
import { ElevenLabsParam, DEFAULT_ELEVEN_LABS_PARAM } from "@/features/constants/elevenLabsParam";
import { buildUrl } from "@/utils/buildUrl";
import { websocketService } from '../services/websocketService';
import { MessageMiddleOut } from "@/features/messages/messageMiddleOut";
import { StatusIndicator } from "@/components/statusIndicator";

// 使用系统字体替代 Google Fonts，避免构建时网络依赖
const m_plus_2 = {
  variable: "--font-m-plus-2",
  className: "",
};

const montserrat = {
  variable: "--font-montserrat",
  className: "",
};

type LLMCallbackResult = {
  processed: boolean;
  error?: string;
};

export default function Home() {
  const { viewer } = useContext(ViewerContext);

  const [systemPrompt, setSystemPrompt] = useState(SYSTEM_PROMPT);
  const [openAiKey, setOpenAiKey] = useState("");
  const [elevenLabsKey, setElevenLabsKey] = useState("");
  const [elevenLabsParam, setElevenLabsParam] = useState<ElevenLabsParam>(DEFAULT_ELEVEN_LABS_PARAM);
  const [koeiroParam, setKoeiroParam] = useState<KoeiroParam>(DEFAULT_KOEIRO_PARAM);
  const [chatProcessing, setChatProcessing] = useState(false);
  const [chatLog, setChatLog] = useState<Message[]>([]);
  const [assistantMessage, setAssistantMessage] = useState("");
  const [backgroundImage, setBackgroundImage] = useState<string>('');
  const [restreamTokens, setRestreamTokens] = useState<any>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  // needed because AI speaking could involve multiple audios being played in sequence
  const [isAISpeaking, setIsAISpeaking] = useState(false);
  const [openRouterKey, setOpenRouterKey] = useState<string>(''); // 不要在初始化时访问localStorage
  
  // FastAPI 认证状态管理
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'error'>('disconnected');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [useFastApi, setUseFastApi] = useState(true); // 默认使用 FastAPI
  const [isMounted, setIsMounted] = useState(false); // 用于避免 hydration mismatch

  // 首次挂载标记（避免hydration错误）
  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isMounted) return;
    
    if (window.localStorage.getItem("chatVRMParams")) {
      const params = JSON.parse(
        window.localStorage.getItem("chatVRMParams") as string
      );
      setSystemPrompt(params.systemPrompt);
      setElevenLabsParam(params.elevenLabsParam);
      setChatLog(params.chatLog);
    }
    if (window.localStorage.getItem("elevenLabsKey")) {
      const key = window.localStorage.getItem("elevenLabsKey") as string;
      setElevenLabsKey(key);
    }
    // load openrouter key from localStorage
    const savedOpenRouterKey = localStorage.getItem('openRouterKey');
    if (savedOpenRouterKey) {
      setOpenRouterKey(savedOpenRouterKey);
    }
    const savedBackground = localStorage.getItem('backgroundImage');
    if (savedBackground) {
      setBackgroundImage(savedBackground);
    }
  }, [isMounted]);

  // 监听来自FastAPI的token消息
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // 验证消息来源
      if (event.origin !== 'http://localhost:8000') {
        return;
      }
      
      if (event.data.type === 'SET_TOKEN' && event.data.token) {
        console.log('✅ 收到来自FastAPI的token');
        // 保存token到localStorage
        localStorage.setItem('access_token', event.data.token);
        localStorage.setItem('userToken', event.data.token);
        // 不刷新页面，直接更新登录状态
        setIsLoggedIn(true);
        setConnectionStatus('connected');
      }
    };
    
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  // 检查 FastAPI 登录状态
  useEffect(() => {
    if (!isMounted) return;
    
    const checkAuth = async () => {
      const token = getAuthToken();
      if (token) {
        const valid = await validateToken(token);
        setIsLoggedIn(valid);
        setConnectionStatus(valid ? 'connected' : 'error');
        
        // 如果 token 无效，清除本地存储并提示用户
        if (!valid) {
          console.warn('⚠️ Token 已失效，需要重新登录');
          localStorage.removeItem('access_token');
          localStorage.removeItem('userToken');
          alert('登录已过期，请关闭此页面并从教育应用重新打开');
        }
      } else {
        setIsLoggedIn(false);
        setConnectionStatus('disconnected');
      }
    };
    checkAuth();
    
    // 每隔 5 分钟检查一次 token 有效性
    const intervalId = setInterval(checkAuth, 5 * 60 * 1000);
    
    return () => clearInterval(intervalId);
  }, [isMounted]);
  
  // 登录成功回调
  const handleLoginSuccess = useCallback(() => {
    const checkAuth = async () => {
      const token = getAuthToken();
      if (token) {
        const valid = await validateToken(token);
        setIsLoggedIn(valid);
        setConnectionStatus(valid ? 'connected' : 'error');
      }
    };
    checkAuth();
  }, []);

  useEffect(() => {
    if (!isMounted) return;
    
    // 保存聊天参数到localStorage
    window.localStorage.setItem(
      "chatVRMParams",
      JSON.stringify({ systemPrompt, elevenLabsParam, chatLog })
    );

    // store separately to be backward compatible with local storage data
    window.localStorage.setItem("elevenLabsKey", elevenLabsKey);
  }, [isMounted, systemPrompt, elevenLabsParam, chatLog, elevenLabsKey]);

  useEffect(() => {
    if (backgroundImage) {
      document.body.style.backgroundImage = `url(${backgroundImage})`;
      // document.body.style.backgroundSize = 'cover';
      // document.body.style.backgroundPosition = 'center';
    } else {
      document.body.style.backgroundImage = `url(${buildUrl("/bg-c.png")})`;
    }
  }, [backgroundImage]);

  const handleChangeChatLog = useCallback(
    (targetIndex: number, text: string) => {
      const newChatLog = chatLog.map((v: Message, i) => {
        return i === targetIndex ? { role: v.role, content: text } : v;
      });

      setChatLog(newChatLog);
    },
    [chatLog]
  );

  /**
   * 文ごとに音声を直接でリクエストしながら再生する
   */
  const handleSpeakAi = useCallback(
    async (
      screenplay: Screenplay,
      elevenLabsKey: string,
      elevenLabsParam: ElevenLabsParam,
      onStart?: () => void,
      onEnd?: () => void
    ) => {
      setIsAISpeaking(true);  // Set speaking state before starting
      try {
        await speakCharacter(
          screenplay, 
          elevenLabsKey, 
          elevenLabsParam, 
          viewer, 
          () => {
            setIsPlayingAudio(true);
            console.log('audio playback started');
            onStart?.();
          }, 
          () => {
            setIsPlayingAudio(false);
            console.log('audio playback completed');
            onEnd?.();
          }
        );
      } catch (error) {
        console.error('Error during AI speech:', error);
      } finally {
        setIsAISpeaking(false);  // Ensure speaking state is reset even if there's an error
      }
    },
    [viewer]
  );

  /**
   * アシスタントとの会話を行う
   */
  const handleSendChat = useCallback(
    async (text: string) => {
      const newMessage = text;
      if (newMessage == null) return;

      setChatProcessing(true);
      // Add user's message to chat log
      const messageLog: Message[] = [
        ...chatLog,
        { role: "user", content: newMessage },
      ];
      setChatLog(messageLog);

      // Process messages through MessageMiddleOut
      const messageProcessor = new MessageMiddleOut();
      const processedMessages = messageProcessor.process([
        {
          role: "system",
          content: systemPrompt,
        },
        ...messageLog,
      ]);

      // 优先使用 FastAPI，如果未登录则使用 OpenRouter 降级
      let stream: ReadableStream<string> | null = null;
      
      console.log('📊 状态检查:', {
        useFastApi,
        isLoggedIn,
        hasToken: !!getAuthToken()
      });
      
      if (useFastApi && isLoggedIn) {
        const token = getAuthToken();
        if (token) {
          console.log('✅ 使用通义千问 API');
          stream = await getQwenChatResponseStream(processedMessages).catch(
            (e) => {
              console.error('❌ 通义千问 API 调用失败:', e);
              return null;
            }
          );
        } else {
          console.warn('⚠️ Token不存在，无法调用API');
        }
      } else {
        console.log('⚠️ 跳过通义千问 API:', {
          useFastApi,
          isLoggedIn
        });
      }
      
      // 降级到 OpenRouter
      if (stream == null) {
        console.log('📱 使用 OpenRouter 降级方案');
        let localOpenRouterKey = openRouterKey;
        if (!localOpenRouterKey) {
          // fallback to free key for users to try things out
          localOpenRouterKey = process.env.NEXT_PUBLIC_OPENROUTER_API_KEY!;
        }

        stream = await getChatResponseStream(processedMessages, openAiKey, localOpenRouterKey).catch(
          (e) => {
            console.error(e);
            return null;
          }
        );
      }
      
      if (stream == null) {
        setChatProcessing(false);
        return;
      }

      const reader = stream.getReader();
      let receivedMessage = "";
      let aiTextLog = "";
      let tag = "";
      const sentences = new Array<string>();
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          receivedMessage += value;

          // console.log('receivedMessage');
          // console.log(receivedMessage);

          // 返答内容のタグ部分の検出
          const tagMatch = receivedMessage.match(/^\[(.*?)\]/);
          if (tagMatch && tagMatch[0]) {
            tag = tagMatch[0];
            receivedMessage = receivedMessage.slice(tag.length);

            console.log('tag:');
            console.log(tag);
          }

          // 返答を一単位で切り出して処理する（优化中文句子分割）
          const sentenceMatch = receivedMessage.match(
            /^(.+?[。！？\n]|.{15,}[，、；])/
          );
          if (sentenceMatch && sentenceMatch[0]) {
            const sentence = sentenceMatch[0];
            sentences.push(sentence);

            console.log('sentence:');
            console.log(sentence);

            receivedMessage = receivedMessage
              .slice(sentence.length)
              .trimStart();

            // 発話不要/不可能な文字列だった場合はスキップ
            if (
              !sentence.replace(
                /^[\s\[\(\{「［（【『〈《〔｛«‹〘〚〛〙›»〕》〉』】）］」\}\)\]]+$/g,
                ""
              )
            ) {
              continue;
            }

            const aiText = `${tag} ${sentence}`;
            const aiTalks = textsToScreenplay([aiText], koeiroParam);
            aiTextLog += aiText;

            // 文ごとに音声を生成 & 再生、返答を表示
            const currentAssistantMessage = sentences.join(" ");
            handleSpeakAi(aiTalks[0], elevenLabsKey, elevenLabsParam, () => {
              setAssistantMessage(currentAssistantMessage);
            });
          }
        }
      } catch (e) {
        setChatProcessing(false);
        console.error(e);
      } finally {
        reader.releaseLock();
      }

      // アシスタントの返答をログに追加
      const messageLogAssistant: Message[] = [
        ...messageLog,
        { role: "assistant", content: aiTextLog },
      ];

      setChatLog(messageLogAssistant);
      setChatProcessing(false);
    },
    [systemPrompt, chatLog, handleSpeakAi, openAiKey, elevenLabsKey, elevenLabsParam, openRouterKey, isLoggedIn, useFastApi, koeiroParam]
  );

  const handleTokensUpdate = useCallback((tokens: any) => {
    setRestreamTokens(tokens);
  }, []);

  // Set up global websocket handler
  useEffect(() => {
    websocketService.setLLMCallback(async (message: string): Promise<LLMCallbackResult> => {
      try {
        if (isAISpeaking || isPlayingAudio || chatProcessing) {
          console.log('Skipping message processing - system busy');
          return {
            processed: false,
            error: 'System is busy processing previous message'
          };
        }
        
        await handleSendChat(message);
        return {
          processed: true
        };
      } catch (error) {
        console.error('Error processing message:', error);
        return {
          processed: false,
          error: error instanceof Error ? error.message : 'Unknown error occurred'
        };
      }
    });
  }, [handleSendChat, chatProcessing, isPlayingAudio, isAISpeaking]);

  const handleOpenRouterKeyChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newKey = event.target.value;
    setOpenRouterKey(newKey);
    localStorage.setItem('openRouterKey', newKey);
  };

  return (
    <div className={`${m_plus_2.variable} ${montserrat.variable}`}>
      <Meta />
      <StatusIndicator status={connectionStatus} isLoggedIn={isLoggedIn} />
      <Introduction
        openAiKey={openAiKey}
        onChangeAiKey={setOpenAiKey}
        elevenLabsKey={elevenLabsKey}
        onChangeElevenLabsKey={setElevenLabsKey}
      />
      <VrmViewer />
      <MessageInputContainer
        isChatProcessing={chatProcessing}
        onChatProcessStart={handleSendChat}
      />
      <Menu
        openAiKey={openAiKey}
        elevenLabsKey={elevenLabsKey}
        openRouterKey={openRouterKey}
        systemPrompt={systemPrompt}
        chatLog={chatLog}
        elevenLabsParam={elevenLabsParam}
        koeiroParam={koeiroParam}
        assistantMessage={assistantMessage}
        onChangeAiKey={setOpenAiKey}
        onChangeElevenLabsKey={setElevenLabsKey}
        onChangeSystemPrompt={setSystemPrompt}
        onChangeChatLog={handleChangeChatLog}
        onChangeElevenLabsParam={setElevenLabsParam}
        onChangeKoeiromapParam={setKoeiroParam}
        handleClickResetChatLog={() => setChatLog([])}
        handleClickResetSystemPrompt={() => setSystemPrompt(SYSTEM_PROMPT)}
        backgroundImage={backgroundImage}
        onChangeBackgroundImage={setBackgroundImage}
        onTokensUpdate={handleTokensUpdate}
        onChatMessage={handleSendChat}
        onChangeOpenRouterKey={handleOpenRouterKeyChange}
        onLoginSuccess={handleLoginSuccess}
      />
      {/* <GitHubLink /> */}
    </div>
  );
}
