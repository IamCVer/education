// 管理服务
class AdminService {
    constructor() {
        this.baseUrl = window.APP_CONFIG ? window.APP_CONFIG.API.BASE_URL : 'http://localhost:8000';
    }
    
    // 触发知识图谱索引
    async indexKnowledgeGraph() {
        const token = window.authService ? window.authService.getToken() : localStorage.getItem('userToken');
        
        if (!token) {
            throw new Error('未登录，请先登录');
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/admin/index-knowledge-graph`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '索引失败');
            }
            
            return await response.json();
        } catch (error) {
            console.error('知识图谱索引失败:', error);
            throw error;
        }
    }
    
    // 获取系统状态
    async getSystemStatus() {
        const token = window.authService ? window.authService.getToken() : localStorage.getItem('userToken');
        
        if (!token) {
            throw new Error('未登录，请先登录');
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/admin/system-status`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '获取系统状态失败');
            }
            
            return await response.json();
        } catch (error) {
            console.error('获取系统状态失败:', error);
            throw error;
        }
    }
    
    // 获取用户列表
    async getUserList() {
        const token = window.authService ? window.authService.getToken() : localStorage.getItem('userToken');
        
        if (!token) {
            throw new Error('未登录，请先登录');
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/admin/users`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '获取用户列表失败');
            }
            
            return await response.json();
        } catch (error) {
            console.error('获取用户列表失败:', error);
            throw error;
        }
    }
    
    // 更新用户状态
    async updateUserStatus(userId, isActive) {
        const token = window.authService ? window.authService.getToken() : localStorage.getItem('userToken');
        
        if (!token) {
            throw new Error('未登录，请先登录');
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/admin/users/${userId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    is_active: isActive
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '更新用户状态失败');
            }
            
            return await response.json();
        } catch (error) {
            console.error('更新用户状态失败:', error);
            throw error;
        }
    }
    
    // 删除用户
    async deleteUser(userId) {
        const token = window.authService ? window.authService.getToken() : localStorage.getItem('userToken');
        
        if (!token) {
            throw new Error('未登录，请先登录');
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/admin/users/${userId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '删除用户失败');
            }
            
            return await response.json();
        } catch (error) {
            console.error('删除用户失败:', error);
            throw error;
        }
    }
    
    // 获取问答统计
    async getQAStatistics() {
        const token = window.authService ? window.authService.getToken() : localStorage.getItem('userToken');
        
        if (!token) {
            throw new Error('未登录，请先登录');
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/admin/qa-statistics`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '获取问答统计失败');
            }
            
            return await response.json();
        } catch (error) {
            console.error('获取问答统计失败:', error);
            throw error;
        }
    }
    
    // 检查管理员权限
    checkAdminPermission() {
        const userInfo = window.authService ? window.authService.getUserInfo() : null;
        if (!userInfo) {
            return false;
        }
        
        // 检查用户角色是否为管理员
        return userInfo.role === 'admin' || userInfo.role === 'administrator';
    }
    
    // 重定向到登录页面（如果不是管理员）
    redirectIfNotAdmin() {
        if (!this.checkAdminPermission()) {
            if (window.Utils) {
                window.Utils.showError('您没有管理员权限');
            }
            setTimeout(() => {
                window.location.href = '/pages/auth/login.html';
            }, 2000);
            return false;
        }
        return true;
    }
}

// 创建全局实例
window.adminService = new AdminService();
