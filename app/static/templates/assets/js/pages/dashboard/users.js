// 用户管理页面逻辑
class UsersPage {
    constructor() {
        this.users = [];
        this.currentPage = 1;
        this.pageSize = 10;
        this.init();
    }
    
    init() {
        this.checkAuth();
        this.bindEvents();
        this.loadUsers();
    }
    
    checkAuth() {
        if (!window.authService || !window.authService.isLoggedIn()) {
            window.location.href = '/pages/auth/login.html';
            return;
        }
    }
    
    bindEvents() {
        // 绑定搜索功能
        const searchInput = document.getElementById('userSearch');
        if (searchInput) {
            searchInput.addEventListener('input', window.Utils.debounce((e) => {
                this.searchUsers(e.target.value);
            }, 300));
        }
        
        // 绑定刷新按钮
        const refreshBtn = document.getElementById('refreshUsers');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadUsers();
            });
        }
    }
    
    async loadUsers() {
        try {
            this.showLoading(true);
            
            const response = await window.adminService.getUserList();
            this.users = response.users || response || [];
            
            this.renderUsers();
            
        } catch (error) {
            console.error('加载用户列表失败:', error);
            window.Utils.showError('加载用户列表失败: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }
    
    renderUsers() {
        const userTableBody = document.getElementById('userTableBody');
        
        if (!userTableBody) return;
        
        // 清空表格
        userTableBody.innerHTML = '';
        
        if (this.users.length === 0) {
            userTableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted">
                        暂无用户数据
                    </td>
                </tr>
            `;
            return;
        }
        
        // 渲染用户行
        this.users.forEach(user => {
            const row = this.createUserRow(user);
            userTableBody.appendChild(row);
        });
    }
    
    createUserRow(user) {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${user.id}</td>
            <td>${user.email || user.username}</td>
            <td>${user.role || 'student'}</td>
            <td>
                <span class="badge badge-${user.is_active ? 'success' : 'danger'}">
                    ${user.is_active ? '活跃' : '禁用'}
                </span>
            </td>
            <td>${window.Utils.formatDate(user.created_at || new Date(), 'YYYY-MM-DD')}</td>
            <td>
                <div class="btn-group" role="group">
                    <button type="button" class="btn btn-sm btn-${user.is_active ? 'warning' : 'success'}" 
                            onclick="usersPage.toggleUserStatus(${user.id}, ${!user.is_active})">
                        ${user.is_active ? '禁用' : '启用'}
                    </button>
                    <button type="button" class="btn btn-sm btn-danger" 
                            onclick="usersPage.deleteUser(${user.id})">
                        删除
                    </button>
                </div>
            </td>
        `;
        
        return row;
    }
    
    async toggleUserStatus(userId, isActive) {
        if (!confirm(`确定要${isActive ? '启用' : '禁用'}该用户吗？`)) {
            return;
        }
        
        try {
            await window.adminService.updateUserStatus(userId, isActive);
            
            // 更新本地数据
            const userIndex = this.users.findIndex(u => u.id === userId);
            if (userIndex !== -1) {
                this.users[userIndex].is_active = isActive;
                this.renderUsers();
            }
            
            window.Utils.showSuccess(`用户已${isActive ? '启用' : '禁用'}`);
            
        } catch (error) {
            console.error('更新用户状态失败:', error);
            window.Utils.showError('更新用户状态失败: ' + error.message);
        }
    }
    
    async deleteUser(userId) {
        if (!confirm('确定要删除该用户吗？此操作不可恢复！')) {
            return;
        }
        
        try {
            await window.adminService.deleteUser(userId);
            
            // 从本地数据中移除
            this.users = this.users.filter(u => u.id !== userId);
            this.renderUsers();
            
            window.Utils.showSuccess('用户已删除');
            
        } catch (error) {
            console.error('删除用户失败:', error);
            window.Utils.showError('删除用户失败: ' + error.message);
        }
    }
    
    searchUsers(keyword) {
        if (!keyword.trim()) {
            this.renderUsers();
            return;
        }
        
        const filteredUsers = this.users.filter(user => 
            user.email?.toLowerCase().includes(keyword.toLowerCase()) ||
            user.username?.toLowerCase().includes(keyword.toLowerCase()) ||
            user.role?.toLowerCase().includes(keyword.toLowerCase())
        );
        
        this.renderFilteredUsers(filteredUsers);
    }
    
    renderFilteredUsers(filteredUsers) {
        const userTableBody = document.getElementById('userTableBody');
        
        if (!userTableBody) return;
        
        userTableBody.innerHTML = '';
        
        if (filteredUsers.length === 0) {
            userTableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted">
                        未找到匹配的用户
                    </td>
                </tr>
            `;
            return;
        }
        
        filteredUsers.forEach(user => {
            const row = this.createUserRow(user);
            userTableBody.appendChild(row);
        });
    }
    
    showLoading(show) {
        const loadingSpinner = document.getElementById('loadingSpinner');
        const userTable = document.getElementById('userTable');
        
        if (loadingSpinner) {
            loadingSpinner.style.display = show ? 'block' : 'none';
        }
        
        if (userTable) {
            userTable.style.opacity = show ? '0.5' : '1';
        }
    }
}

// 创建全局实例
let usersPage;
document.addEventListener('DOMContentLoaded', () => {
    usersPage = new UsersPage();
});
