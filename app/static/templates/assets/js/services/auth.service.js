// 认证服务
class AuthService {
    constructor() {
        this.baseUrl = window.APP_CONFIG ? window.APP_CONFIG.API.BASE_URL : 'http://localhost:8000';
    }
    
    // 用户登录
    async login(username, password) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '登录失败');
            }
            
            return await response.json();
        } catch (error) {
            console.error('登录请求失败:', error);
            throw error;
        }
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
                const error = await response.json();
                throw new Error(error.detail || '注册失败');
            }
            
            return await response.json();
        } catch (error) {
            console.error('注册请求失败:', error);
            throw error;
        }
    }
    
    // 检查登录状态
    isLoggedIn() {
        const token = localStorage.getItem('userToken');
        return !!token;
    }
    
    // 获取用户信息
    getUserInfo() {
        const userInfo = localStorage.getItem('userInfo');
        return userInfo ? JSON.parse(userInfo) : null;
    }
    
    // 获取用户ID
    getUserId() {
        const userInfo = this.getUserInfo();
        return userInfo ? userInfo.id : null;
    }
    
    // 获取访问令牌
    getToken() {
        return localStorage.getItem('userToken');
    }
    
    // 解析JWT token获取用户信息
    parseUserInfoFromToken(token, username) {
        try {
            const tokenParts = token.split('.');
            if (tokenParts.length === 3) {
                const payload = JSON.parse(atob(tokenParts[1]));
                return {
                    id: parseInt(payload.sub) || 1,
                    username: username,
                    email: username
                };
            }
        } catch (e) {
            console.warn('无法解析JWT token，使用默认用户信息');
        }
        
        return {
            id: 1,
            username: username,
            email: username
        };
    }
    
    // 保存用户信息
    saveUserInfo(token, username, password = null) {
        localStorage.setItem('userToken', token);
        
        const userInfo = this.parseUserInfoFromToken(token, username);
        localStorage.setItem('userInfo', JSON.stringify(userInfo));
        
        // 保存记住密码
        if (password) {
            const rememberPassword = localStorage.getItem('rememberPassword') === 'true';
            if (rememberPassword) {
                localStorage.setItem('userName', username);
                localStorage.setItem('passWord', password);
            }
        }
    }
    
    // 加载保存的凭据
    loadSavedCredentials() {
        const rememberPassword = localStorage.getItem('rememberPassword') === 'true';
        if (rememberPassword) {
            const savedUsername = localStorage.getItem('userName');
            const savedPassword = localStorage.getItem('passWord');
            
            return {
                username: savedUsername,
                password: savedPassword,
                rememberPassword: true
            };
        }
        return null;
    }
    
    // 退出登录
    logout() {
        localStorage.removeItem('userToken');
        localStorage.removeItem('userInfo');
        localStorage.removeItem('userName');
        localStorage.removeItem('passWord');
        
        // 跳转到登录页面
        window.location.href = '/pages/auth/login.html';
    }
    
    // 检查令牌是否过期
    isTokenExpired() {
        const token = this.getToken();
        if (!token) return true;
        
        try {
            const tokenParts = token.split('.');
            if (tokenParts.length === 3) {
                const payload = JSON.parse(atob(tokenParts[1]));
                const currentTime = Math.floor(Date.now() / 1000);
                return payload.exp < currentTime;
            }
        } catch (e) {
            console.warn('无法解析token过期时间');
        }
        
        return true;
    }
    
    // 刷新令牌（如果需要的话）
    async refreshToken() {
        // 这里可以实现令牌刷新逻辑
        // 目前简单返回false表示不需要刷新
        return false;
    }
}

// 创建全局实例
window.authService = new AuthService();
