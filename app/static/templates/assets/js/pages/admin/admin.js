// 管理后台页面逻辑
class AdminPage {
    constructor() {
        this.init();
    }
    
    init() {
        this.checkAuth();
        this.bindEvents();
        this.loadSystemInfo();
    }
    
    checkAuth() {
        if (!window.authService || !window.authService.isLoggedIn()) {
            window.location.href = '/pages/auth/login.html';
            return;
        }
        
        // 检查管理员权限
        if (window.adminService && !window.adminService.checkAdminPermission()) {
            window.Utils.showError('您没有管理员权限');
            setTimeout(() => {
                window.location.href = '/pages/dashboard/chat.html';
            }, 2000);
        }
    }
    
    bindEvents() {
        // 绑定知识图谱索引按钮
        const indexBtn = document.getElementById('indexBtn');
        if (indexBtn) {
            indexBtn.addEventListener('click', () => {
                this.triggerIndex();
            });
        }
        
        // 绑定系统状态刷新按钮
        const refreshBtn = document.getElementById('refreshSystemInfo');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadSystemInfo();
            });
        }
        
        // 绑定日志清除按钮
        const clearLogsBtn = document.getElementById('clearLogs');
        if (clearLogsBtn) {
            clearLogsBtn.addEventListener('click', () => {
                this.clearLogs();
            });
        }
    }
    
    async loadSystemInfo() {
        try {
            const response = await window.adminService.getSystemStatus();
            this.updateSystemInfo(response);
        } catch (error) {
            console.error('加载系统信息失败:', error);
            // 如果API不存在，显示默认信息
            this.updateSystemInfo({
                system_status: '运行中',
                uptime: '未知',
                memory_usage: '未知',
                cpu_usage: '未知',
                last_index_time: '未知'
            });
        }
    }
    
    updateSystemInfo(info) {
        // 更新系统状态
        const statusEl = document.getElementById('systemStatus');
        if (statusEl) {
            statusEl.textContent = info.system_status || '运行中';
            statusEl.className = `badge badge-${info.system_status === '运行中' ? 'success' : 'warning'}`;
        }
        
        // 更新运行时间
        const uptimeEl = document.getElementById('systemUptime');
        if (uptimeEl) {
            uptimeEl.textContent = info.uptime || '未知';
        }
        
        // 更新内存使用
        const memoryEl = document.getElementById('memoryUsage');
        if (memoryEl) {
            memoryEl.textContent = info.memory_usage || '未知';
        }
        
        // 更新CPU使用
        const cpuEl = document.getElementById('cpuUsage');
        if (cpuEl) {
            cpuEl.textContent = info.cpu_usage || '未知';
        }
        
        // 更新最后索引时间
        const lastIndexEl = document.getElementById('lastIndexTime');
        if (lastIndexEl) {
            lastIndexEl.textContent = info.last_index_time || '未知';
        }
    }
    
    async triggerIndex() {
        const indexBtn = document.getElementById('indexBtn');
        const progressBar = document.getElementById('indexProgress');
        
        try {
            // 禁用按钮
            indexBtn.disabled = true;
            indexBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 索引中...';
            
            // 更新状态
            this.updateIndexStatus('warning', '正在索引...');
            this.addLog('开始触发知识图谱索引...', 'info');
            
            // 模拟进度条
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += Math.random() * 10;
                if (progress > 90) progress = 90;
                if (progressBar) {
                    progressBar.style.width = progress + '%';
                }
            }, 200);
            
            // 调用索引API
            const result = await window.adminService.indexKnowledgeGraph();
            
            // 清除进度条定时器
            clearInterval(progressInterval);
            
            // 完成进度条
            if (progressBar) {
                progressBar.style.width = '100%';
            }
            
            // 更新状态
            this.updateIndexStatus('success', '索引完成');
            this.addLog(`索引成功: ${result.detail}`, 'success');
            
            // 更新最后索引时间
            const lastIndexEl = document.getElementById('lastIndexTime');
            if (lastIndexEl) {
                lastIndexEl.textContent = new Date().toLocaleString();
            }
            
        } catch (error) {
            console.error('索引失败:', error);
            this.updateIndexStatus('error', '索引失败');
            this.addLog(`索引失败: ${error.message}`, 'error');
        } finally {
            // 恢复按钮
            indexBtn.disabled = false;
            indexBtn.innerHTML = '<i class="fas fa-sync-alt"></i> 触发知识图谱索引';
        }
    }
    
    updateIndexStatus(type, message) {
        const statusEl = document.getElementById('indexStatus');
        if (statusEl) {
            statusEl.textContent = message;
            statusEl.className = `badge badge-${type}`;
        }
    }
    
    addLog(message, type = 'info') {
        const logsContainer = document.getElementById('logsContainer');
        if (!logsContainer) return;
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        
        const timestamp = new Date().toLocaleTimeString();
        logEntry.innerHTML = `
            <span class="log-time">[${timestamp}]</span>
            <span class="log-message">${message}</span>
        `;
        
        logsContainer.appendChild(logEntry);
        
        // 自动滚动到底部
        logsContainer.scrollTop = logsContainer.scrollHeight;
        
        // 限制日志数量
        const logEntries = logsContainer.querySelectorAll('.log-entry');
        if (logEntries.length > 100) {
            logEntries[0].remove();
        }
    }
    
    clearLogs() {
        const logsContainer = document.getElementById('logsContainer');
        if (logsContainer) {
            logsContainer.innerHTML = '';
            this.addLog('日志已清除', 'info');
        }
    }
    
    // 导出系统信息
    exportSystemInfo() {
        const systemInfo = {
            timestamp: new Date().toISOString(),
            system_status: document.getElementById('systemStatus')?.textContent || '未知',
            uptime: document.getElementById('systemUptime')?.textContent || '未知',
            memory_usage: document.getElementById('memoryUsage')?.textContent || '未知',
            cpu_usage: document.getElementById('cpuUsage')?.textContent || '未知',
            last_index_time: document.getElementById('lastIndexTime')?.textContent || '未知'
        };
        
        const dataStr = JSON.stringify(systemInfo, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `system_info_${window.Utils.formatDate(new Date(), 'YYYY-MM-DD_HH-mm-ss')}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
    
    // 实时更新系统信息
    startRealTimeUpdates() {
        // 每30秒更新一次系统信息
        setInterval(() => {
            this.loadSystemInfo();
        }, 30000);
    }
}

// 创建全局实例
let adminPage;
document.addEventListener('DOMContentLoaded', () => {
    adminPage = new AdminPage();
    // 启动实时更新
    adminPage.startRealTimeUpdates();
});
