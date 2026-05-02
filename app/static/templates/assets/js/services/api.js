// API工具类 - 封装所有后端接口调用
class ApiService {
    constructor() {
        this.baseUrl = window.API_CONFIG ? window.API_CONFIG.BASE_URL : 'http://localhost:8000';
        this.wsUrl = window.API_CONFIG ? window.API_CONFIG.WS_BASE_URL : 'ws://localhost:8000';
    }

    // 获取认证token
    getToken() {
        return localStorage.getItem('userToken');
    }

    // 获取用户信息
    getUserInfo() {
        const userInfo = localStorage.getItem('userInfo');
        return userInfo ? JSON.parse(userInfo) : null;
    }

    // 设置认证头
    getAuthHeaders() {
        const token = this.getToken();
        return {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
        };
    }

    // 用户注册
    async register(email, password, role = 'student') {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: email,
                    password: password,
                    role: role
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('注册失败:', error);
            throw error;
        }
    }

    // 用户登录
    async login(username, password) {
        try {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('登录失败:', error);
            throw error;
        }
    }

    // 提交问题
    async submitQuestion(text, forceRegenerate = false) {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/questions`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify({
                    text: text,
                    force_regenerate: forceRegenerate
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('提交问题失败:', error);
            throw error;
        }
    }

    // 建立WebSocket连接
    createWebSocketConnection(userId) {
        try {
            const ws = new WebSocket(`${this.wsUrl}/ws/qa?token=${userId}`);
            return ws;
        } catch (error) {
            console.error('建立WebSocket连接失败:', error);
            throw error;
        }
    }

    // 管理员接口：触发知识图谱索引
    async indexKnowledgeGraph() {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/admin/index-knowledge-graph`, {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('索引知识图谱失败:', error);
            throw error;
        }
    }

    // 检查用户是否已登录
    isLoggedIn() {
        const token = this.getToken();
        return !!token;
    }

    // 登出
    logout() {
        localStorage.removeItem('userToken');
        localStorage.removeItem('userInfo');
        localStorage.removeItem('userName');
        localStorage.removeItem('passWord');
        localStorage.removeItem('check1');
        localStorage.removeItem('check2');
    }

    // 解析JWT token获取用户ID
    parseUserIdFromToken(token) {
        try {
            const tokenParts = token.split('.');
            if (tokenParts.length === 3) {
                const payload = JSON.parse(atob(tokenParts[1]));
                return payload.sub ? parseInt(payload.sub) : null;
            }
        } catch (error) {
            console.warn('解析JWT token失败:', error);
        }
        return null;
    }
}

// 创建全局API服务实例
window.apiService = new ApiService();
