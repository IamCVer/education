// 问答服务 (最终架构修正版)
class QAService {
    constructor() {
        this.baseUrl = window.APP_CONFIG ? window.APP_CONFIG.API.BASE_URL : 'http://localhost:8000';
        this.wsUrl = window.APP_CONFIG ? window.APP_CONFIG.API.WS_URL : 'ws://localhost:8000';
        this.ws = null;
        // ✅ 修正：不再使用Map，而是用一个单一的全局处理器
        this.globalMessageHandler = null;
    }

    async submitQuestion(text, forceRegenerate = false) {
        // (此函数无任何变化)
        const token = window.authService ? window.authService.getToken() : localStorage.getItem('userToken');
        if (!token) { throw new Error('未登录，请先登录'); }
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/questions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ text: text, force_regenerate: forceRegenerate })
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '提交问题失败');
            }
            return await response.json();
        } catch (error) {
            console.error('提交问题失败:', error);
            throw error;
        }
    }

    createWebSocketConnection() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) { return this.ws; }
        const accessToken = window.authService ? window.authService.getToken() : null;
        if (!accessToken) {
            console.error('无法建立WebSocket连接：找不到access_token，请先登录。');
            if (window.Utils) { window.Utils.showError('认证信息丢失，无法建立实时连接'); }
            return;
        }
        const wsUrl = `${this.wsUrl}/api/v1/ws/qa?token=${accessToken}`;
        console.log('建立WebSocket连接:', wsUrl);
        this.ws = new WebSocket(wsUrl);
        this.ws.onopen = () => {
            console.log('WebSocket连接已建立');
            if (window.Utils) { window.Utils.showSuccess('实时连接已建立'); }
        };
        this.ws.onmessage = (event) => {
            // ✅ 修正：直接调用全局处理器
            try {
                const data = JSON.parse(event.data);
                console.log('收到WebSocket消息:', data);
                if (this.globalMessageHandler) {
                    this.globalMessageHandler(data);
                } else {
                    console.warn('收到WebSocket消息，但未注册全局处理器。');
                }
            } catch (error) {
                console.error('解析WebSocket消息失败:', error);
            }
        };
        this.ws.onerror = (error) => {
            console.error('WebSocket连接错误:', error);
            if (window.Utils) { window.Utils.showError('WebSocket连接错误'); }
        };
        this.ws.onclose = (event) => {
            console.log('WebSocket连接已关闭:', event.code, event.reason);
            if (event.code === 4001) {
                console.error('WebSocket认证失败，请重新登录。');
                if (window.Utils) { window.Utils.showError('实时连接认证失败，请重新登录'); }
                return;
            }
            if (window.Utils) { window.Utils.showWarning('实时连接已断开，3秒后尝试重连...'); }
            setTimeout(() => {
                if (this.ws && this.ws.readyState === WebSocket.CLOSED) {
                    this.createWebSocketConnection();
                }
            }, 3000);
        };
        return this.ws;
    }

    // (文件其余部分已简化或移除，因为不再需要)
    closeWebSocketConnection() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    async generateAudio(questionId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/questions/${questionId}/generate-audio`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${window.authService ? window.authService.getToken() : ''}`
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('生成音频API调用失败:', error);
            throw error;
        }
    }
}

window.qaService = new QAService();