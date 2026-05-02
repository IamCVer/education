/**
 * FastAPI后端集成
 * 替换OpenRouter，调用本地FastAPI的LLM接口
 * 
 * 【新增】支持通义千问 DashScope API
 */

import { Message } from "../messages/messages";

// 优先使用显式配置的后端地址，避免在 3001 上误打到 ChatVRM 自身。
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const DASHSCOPE_KEY = process.env.NEXT_PUBLIC_DASHSCOPE_KEY || '';

// 全局持久化WebSocket连接
let globalWs: WebSocket | null = null;
let wsConnecting = false;
const messageHandlers = new Map<string, (data: any) => void>();
const pendingMessages = new Map<string, any[]>(); // 缓存未处理的消息

/**
 * 确保WebSocket连接已建立
 */
async function ensureWebSocketConnection(token: string): Promise<WebSocket> {
  // 如果已经有连接且状态正常，直接返回
  if (globalWs && globalWs.readyState === WebSocket.OPEN) {
    return globalWs;
  }

  // 如果正在连接中，等待连接完成
  if (wsConnecting) {
    await new Promise(resolve => setTimeout(resolve, 100));
    return ensureWebSocketConnection(token);
  }

  // 创建新连接
  wsConnecting = true;
  const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/api/v1/ws/qa?token=${token}`;
  globalWs = new WebSocket(wsUrl);

  return new Promise((resolve, reject) => {
    if (!globalWs) {
      reject(new Error('WebSocket创建失败'));
      return;
    }

    globalWs.onopen = () => {
      console.log('🔗 WebSocket全局连接已建立');
      wsConnecting = false;
      resolve(globalWs!);
    };

    globalWs.onerror = (error) => {
      console.error('❌ WebSocket连接错误:', error);
      wsConnecting = false;
      globalWs = null;
      reject(error);
    };

    globalWs.onclose = () => {
      console.log('🔌 WebSocket全局连接已关闭');
      globalWs = null;
      wsConnecting = false;
    };

    globalWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('📥 收到WebSocket消息:', data);
        
        const questionId = data.question_id;
        const handler = messageHandlers.get(questionId);
        
        if (handler) {
          handler(data);
        } else {
          // 缓存未处理的消息
          console.log('💾 缓存消息，等待处理器注册:', questionId);
          if (!pendingMessages.has(questionId)) {
            pendingMessages.set(questionId, []);
          }
          pendingMessages.get(questionId)!.push(data);
        }
      } catch (error) {
        console.error('解析WebSocket消息失败:', error);
      }
    };
  });
}

// ========== 【C】对话模型：通义千问 DashScope API ==========
/**
 * 调用通义千问 API（流式返回）
 */
export async function getQwenChatResponseStream(messages: Message[]) {
  console.log('📤 调用通义千问 API...');

  const stream = new ReadableStream({
    async start(controller: ReadableStreamDefaultController) {
      try {
        if (!DASHSCOPE_KEY) {
          throw new Error('未配置 DASHSCOPE_KEY 环境变量');
        }

        const requestBody = {
          model: 'qwen-turbo',
          messages: messages.map(m => ({ role: m.role, content: m.content })),
          stream: true,
          temperature: 0.7,
          max_tokens: 500  // 增加 max_tokens
        };
        
        console.log('📤 请求参数:', JSON.stringify(requestBody, null, 2));
        
        const response = await fetch('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${DASHSCOPE_KEY}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error('❌ API 错误详情:', errorText);
          throw new Error(`通义千问 API 错误: ${response.status} - ${errorText}`);
        }

        if (!response.body) {
          throw new Error('响应体为空');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n').filter(line => line.trim().startsWith('data:'));

          for (const line of lines) {
            const jsonStr = line.replace('data:', '').trim();
            if (jsonStr === '[DONE]') continue;

            try {
              const data = JSON.parse(jsonStr);
              const content = data.choices?.[0]?.delta?.content;
              if (content) {
                controller.enqueue(content);
              }
            } catch (e) {
              console.error('解析通义千问响应失败:', e);
            }
          }
        }

        controller.close();
      } catch (error) {
        console.error('❌ 通义千问调用失败:', error);
        controller.error(error);
      }
    }
  });

  return stream;
}

// ========== 【旧代码】FastAPI 后端调用（已注释保留） ==========
/*
export async function getFastApiChatResponseStream(
  messages: Message[],
  token: string
) {
  console.log('📤 调用FastAPI后端...');
  
  const stream = new ReadableStream({
    async start(controller: ReadableStreamDefaultController) {
      let questionId: string | null = null;
      
      try {
        // 1️⃣ 确保WebSocket连接已建立
        await ensureWebSocketConnection(token);
        
        // 2️⃣ 提交问题到FastAPI
        const lastMessage = messages[messages.length - 1];
        const response = await fetch(`${API_BASE_URL}/api/v1/questions`, {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            text: lastMessage.content,
            force_regenerate: false
          })
        });

        if (!response.ok) {
          throw new Error(`FastAPI错误: ${response.status}`);
        }

        const data = await response.json();
        questionId = data.question_id;
        
        if (!questionId) {
          throw new Error('后端未返回 question_id');
        }
        
        console.log('✅ 问题已提交:', questionId);

        // 3️⃣ 注册消息处理器
        const handleMessage = (data: any) => {
          if (data.type === 'answer') {
            // 后端发送完整答案（非流式）
            const answer = data.data?.answer || '';
            console.log('✅ 收到完整答案，长度:', answer.length);
            controller.enqueue(answer);
            controller.close();
            // 清理处理器和缓存
            messageHandlers.delete(questionId!);
            pendingMessages.delete(questionId!);
          } else if (data.type === 'answer_chunk') {
            // 流式推送文本片段
            const content = data.content || '';
            controller.enqueue(content);
          } else if (data.type === 'answer_complete') {
            // 完成
            console.log('✅ 回答完成');
            controller.close();
            messageHandlers.delete(questionId!);
            pendingMessages.delete(questionId!);
          } else if (data.type === 'error') {
            // 错误处理
            console.error('❌ 后端错误:', data.message);
            controller.error(new Error(data.message || '后端处理失败'));
            messageHandlers.delete(questionId!);
            pendingMessages.delete(questionId!);
          }
        };
        
        messageHandlers.set(questionId, handleMessage);
        
        // 4️⃣ 处理可能已经到达的pending消息
        if (pendingMessages.has(questionId)) {
          console.log('🔄 处理缓存的消息:', questionId);
          const messages = pendingMessages.get(questionId)!;
          pendingMessages.delete(questionId);
          messages.forEach(msg => handleMessage(msg));
        }

        // 5️⃣ 设置超时保护（120秒）
        setTimeout(() => {
          if (questionId && messageHandlers.has(questionId)) {
            console.error('⏱️ 等待响应超时');
            controller.error(new Error('等待响应超时'));
            messageHandlers.delete(questionId);
            pendingMessages.delete(questionId);
          }
        }, 120000);

      } catch (error) {
        console.error('❌ FastAPI调用失败:', error);
        if (questionId) {
          messageHandlers.delete(questionId);
          pendingMessages.delete(questionId);
        }
        controller.error(error);
      }
    },
  });

  return stream;
}
*/

/**
 * 获取或提示用户登录
 */
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  
  // 1. 首先尝试从 URL 参数获取 token
  const urlParams = new URLSearchParams(window.location.search);
  const urlToken = urlParams.get('token');
  
  if (urlToken) {
    console.log('📥 从URL获取token，保存到localStorage');
    // 保存到 localStorage
    localStorage.setItem('access_token', urlToken);
    localStorage.setItem('userToken', urlToken);
    
    // 清除 URL 中的 token 参数（安全考虑）
    const url = new URL(window.location.href);
    url.searchParams.delete('token');
    window.history.replaceState({}, document.title, url.toString());
    
    return urlToken;
  }
  
  // 2. 尝试从localStorage获取token
  const token = localStorage.getItem('userToken') || localStorage.getItem('access_token');
  
  if (!token) {
    console.warn('⚠️ 未找到认证token，需要登录');
    return null;
  }
  
  return token;
}

/**
 * 检查是否已登录
 */
export function isAuthenticated(): boolean {
  return getAuthToken() !== null;
}

/**
 * 检查 Token 是否有效
 */
export async function validateToken(token: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * 登录获取 Token
 */
export async function login(username: string, password: string): Promise<string | null> {
  try {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      body: formData
    });
    
    if (response.ok) {
      const data = await response.json();
      const token = data.access_token;
      
      // 保存到 localStorage
      localStorage.setItem('access_token', token);
      localStorage.setItem('userToken', token);
      
      return token;
    }
    return null;
  } catch (error) {
    console.error('登录失败:', error);
    return null;
  }
}

/**
 * 退出登录
 */
export function logout(): void {
  localStorage.removeItem('access_token');
  localStorage.removeItem('userToken');
}

