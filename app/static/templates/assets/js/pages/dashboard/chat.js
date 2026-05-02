// 聊天页面逻辑 (最终架构修正版)
class ChatPage {
    constructor() {
        this.currentConversationId = null;
        this.isWebSocketConnected = false;
        this.init();
    }

    init() {
        this.checkAuth();
        this.bindEvents();
        this.initializeWebSocket();
        this.loadConversationHistory();
    }

    checkAuth() {
        if (!window.authService.isLoggedIn()) {
            window.Utils.showError('请先登录');
            setTimeout(() => { window.location.href = '/pages/auth/login.html'; }, 1500);
            return false;
        }
        return true;
    }

    bindEvents() {
        $('#sendBtn').on('click', () => { this.sendMessage(); });
        $('#messageInput').on('keypress', (e) => {
            if (e.which === 13 && !e.shiftKey) { e.preventDefault(); this.sendMessage(); }
        });

        // vvvvvvvvvvvv 【核心修正】 vvvvvvvvvvvv
        // 在事件绑定时，就注册一个唯一的、持久的WebSocket消息处理器
        // 这个处理器将处理所有未来的WebSocket消息，无论它们何时到达
        window.qaService.globalMessageHandler = (message) => {
            console.log("全局处理器接收到消息:", message);
            switch (message.type) {
                case 'answer':
                    this.hideTypingIndicator();
                    // 确保 message.data 存在
                    if (message.data) {
                        this.addMessage(message.data.answer, 'assistant', message.data.sources, message.question_id);
                    }
                    break;
                case 'audio_generation_started':
                    this.showAudioGenerationStatus('正在生成语音...');
                    break;
                case 'audio_ready':
                    this.hideAudioGenerationStatus();
                    if (message.data && message.data.audio_url && message.question_id) {
                        const $targetMessage = $(`.message[data-question-id="${message.question_id}"]`);
                        if ($targetMessage.length) {
                            this.addAudioToMessage($targetMessage, message.data.audio_url);
                        } else {
                            // 如果找不到具体消息，则添加到最后一条助手消息
                            this.addAudioToLastMessage(message.data.audio_url);
                        }
                    }
                    break;
                case 'audio_error':
                    this.hideAudioGenerationStatus();
                    this.showAudioError(message.message || '语音生成失败');
                    break;
                case 'error':
                    this.hideTypingIndicator();
                    this.addErrorMessage(message.message);
                    break;
                case 'status':
                    // 确保 message.data 存在
                    if (message.data) {
                        this.updateTypingStatus(message.data.status);
                    }
                    break;
                default:
                    console.warn('未知的消息类型:', message.type);
            }
        };
        // ^^^^^^^^^^^^ 【核心修正】 ^^^^^^^^^^^^

        $('#newChatBtn').on('click', () => { this.startNewConversation(); });
        $('#sidebarToggle').on('click', () => { this.toggleSidebar(); });
        $('#copyBtn').on('click', () => { this.copyConversation(); });
        $(document).on('click', '.conversation-item', (e) => {
            const conversationId = $(e.currentTarget).data('id');
            if (conversationId !== this.currentConversationId) { this.loadConversation(conversationId); }
        });
        $(document).on('click', '.conversation-menu', (e) => {
            e.stopPropagation();
            this.showConversationMenu(e.currentTarget);
        });
    }

    async sendMessage() {
        const messageText = $('#messageInput').val().trim();
        if (!messageText) { return; }

        this.addMessage(messageText, 'user');
        $('#messageInput').val('');
        this.showTypingIndicator();

        try {
            // ✅ 修正：现在我们只管发送HTTP请求，不再需要处理响应来注册处理器
            const response = await window.qaService.submitQuestion(messageText);

            // 如果HTTP请求本身失败，我们才需要处理
            if (!response || !response.question_id) {
                this.hideTypingIndicator();
                window.Utils.showError(response.detail || '发送失败');
            }
            // 成功时无需做任何事，等待全局处理器接收WebSocket消息即可

        } catch (error) {
            console.error('发送消息错误:', error);
            this.hideTypingIndicator();
            window.Utils.showError('发送失败，请检查网络连接');
        }
    }

    // (文件其余部分无任何变化, 除了initializeWebSocket)
    initializeWebSocket() {
        // (此函数无任何变化)
        window.qaService.createWebSocketConnection();
    }

    // ... (此处省略所有其他未变化的函数: addMessage, showTypingIndicator等) ...
    // 为了简洁，我将省略所有其他未改变的函数，请您只替换上面已修改的部分，或用这个完整的class替换
    addMessage(text, sender, sources = [], questionId = null) { 
        const audioButton = sender === 'assistant' && questionId ? 
            `<div class="message-actions mt-2">
                <button class="btn btn-sm btn-outline-primary generate-audio-btn" 
                        data-question-id="${questionId}" 
                        onclick="chatPage.generateAudio('${questionId}')">
                    <i class="fas fa-volume-up"></i> 生成语音
                </button>
            </div>` : '';
        
        const messageHtml = `
            <div class="message ${sender}-message" data-question-id="${questionId || ''}">
                <div class="message-avatar">
                    <i class="fas fa-${sender === 'user' ? 'user' : 'robot'}"></i>
                </div>
                <div class="message-content">
                    <div class="message-text">
                        <p>${this.escapeHtml(text)}</p>
                        ${sources.length > 0 ? this.renderSources(sources) : ''}
                    </div>
                    ${audioButton}
                    <div class="message-time">${window.Utils.formatDate(new Date())}</div>
                </div>
            </div>`;
        $('#chatMessages').append(messageHtml); 
        this.scrollToBottom(); 
    }
    addErrorMessage(message) { const errorHtml = `<div class="message assistant-message error"><div class="message-avatar"><i class="fas fa-exclamation-triangle"></i></div><div class="message-content"><div class="message-text"><p class="text-danger">${this.escapeHtml(message)}</p></div><div class="message-time">${window.Utils.formatDate(new Date())}</div></div></div>`; $('#chatMessages').append(errorHtml); this.scrollToBottom(); }
    renderSources(sources) { if (!sources || sources.length === 0) return ''; let sourcesHtml = '<div class="message-sources"><h6>参考来源：</h6><ul>'; sources.forEach(source => { sourcesHtml += `<li><a href="${source.url}" target="_blank">${source.title}</a></li>`; }); sourcesHtml += '</ul></div>'; return sourcesHtml; }
    showTypingIndicator() { const typingHtml = `<div class="message assistant-message typing" id="typingIndicator"><div class="message-avatar"><i class="fas fa-robot"></i></div><div class="message-content"><div class="message-text"><div class="typing-dots"><span></span><span></span><span></span></div></div></div></div>`; $('#chatMessages').append(typingHtml); this.scrollToBottom(); }
    hideTypingIndicator() { $('#typingIndicator').remove(); }
    updateTypingStatus(status) { const $indicator = $('#typingIndicator'); if ($indicator.length) { $indicator.find('.message-text').html(`<p><em>${status}</em></p>`); } }
    
    // === 新增的音频处理方法 ===
    showAudioGenerationStatus(message) {
        // 在最后一条助手消息中添加音频生成状态
        const $lastAssistantMessage = $('.message.assistant-message').last();
        if ($lastAssistantMessage.length) {
            // 移除已存在的音频状态
            $lastAssistantMessage.find('.audio-status').remove();
            
            // 添加音频生成状态
            const statusHtml = `<div class="audio-status text-muted mt-2">
                <i class="fas fa-microphone fa-spin"></i> ${message}
            </div>`;
            $lastAssistantMessage.find('.message-content').append(statusHtml);
            this.scrollToBottom();
        }
    }
    
    hideAudioGenerationStatus() {
        $('.audio-status').fadeOut(300, function() {
            $(this).remove();
        });
    }
    
    addAudioToLastMessage(audioUrl) {
        // 找到最后一条助手消息
        const $lastAssistantMessage = $('.message.assistant-message').last();
        if ($lastAssistantMessage.length) {
            this.addAudioToMessage($lastAssistantMessage, audioUrl);
        }
    }
    
    addAudioToMessage($message, audioUrl) {
        // 若已有播放器则跳过
        if ($message.find('.audio-player-inline').length) return;

        // 优先放入同一行（message-actions 内）
        const $actions = $message.find('.message-actions');
        const audioInline = `<div class="audio-player-inline">
                <audio controls preload="metadata" style="width:300px;">
                    <source src="${audioUrl}" type="audio/wav">
                    您的浏览器不支持音频播放。
                </audio>
            </div>`;

        if ($actions.length) {
            $actions.append(audioInline);
        } else {
            // 回退：追加到 message-content 末尾
            $message.find('.message-content').append(`<div class="mt-2">${audioInline}</div>`);
        }

        // 更新按钮状态
        $message.find('.generate-audio-btn')
            .prop('disabled', true)
            .html('<i class="fas fa-check"></i> 已生成');

        this.scrollToBottom();

        setTimeout(() => {
            window.Utils?.showSuccess('语音已生成');
        }, 100);
    }
    
    showAudioError(message) {
        const $lastAssistantMessage = $('.message.assistant-message').last();
        if ($lastAssistantMessage.length) {
            const errorHtml = `<div class="audio-error text-warning mt-2">
                <i class="fas fa-exclamation-triangle"></i> ${message}
            </div>`;
            $lastAssistantMessage.find('.message-content').append(errorHtml);
            this.scrollToBottom();
            
            // 3秒后自动隐藏错误信息
            setTimeout(() => {
                $('.audio-error').fadeOut(300, function() {
                    $(this).remove();
                });
            }, 3000);
        }
    }
    
    async generateAudio(questionId) {
        console.log(`🔊 生成音频，问题ID: ${questionId}`);
        
        // 禁用按钮并显示加载状态
        const $button = $(`.generate-audio-btn[data-question-id="${questionId}"]`);
        $button.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> 生成中...');
        
        try {
            console.log('🔊 调用API生成音频...');
            const response = await window.qaService.generateAudio(questionId);
            console.log('🔊 API响应:', response);
            
            if (response.error) {
                console.log('🔊 API返回错误:', response.error);
                // 恢复按钮状态
                $button.prop('disabled', false).html('<i class="fas fa-volume-up"></i> 生成语音');
                window.Utils?.showError(response.error);
            } else {
                console.log('🔊 API调用成功，等待WebSocket消息...');
            }
            // 成功的话，音频会通过WebSocket消息返回，在消息处理器中处理
            
        } catch (error) {
            console.error('🔊 生成音频失败:', error);
            $button.prop('disabled', false).html('<i class="fas fa-volume-up"></i> 生成语音');
            window.Utils?.showError('生成音频失败，请稍后重试');
        }
    }
    startNewConversation() { this.currentConversationId = null; $('#conversationTitle').text('新对话'); $('#chatMessages').html(this.getWelcomeMessage()); this.updateActiveConversation('current'); }
    loadConversation(conversationId) { $('#chatMessages').html('<div class="text-center"><i class="fas fa-spinner fa-spin"></i> 加载中...</div>'); setTimeout(() => { $('#chatMessages').html(this.getWelcomeMessage()); this.currentConversationId = conversationId; this.updateActiveConversation(conversationId); }, 1000); }
    loadConversationHistory() { $('#historyList').html('<div class="text-muted text-center">暂无历史对话</div>'); }
    updateActiveConversation(conversationId) { $('.conversation-item').removeClass('active'); $(`.conversation-item[data-id="${conversationId}"]`).addClass('active'); }
    toggleSidebar() { $('#sidebar').toggleClass('collapsed'); $('.main-content').toggleClass('expanded'); }
    copyConversation() { const messages = []; $('.message').each((index, element) => { const $message = $(element); const sender = $message.hasClass('user-message') ? '用户' : 'AI'; const text = $message.find('.message-text p').text(); messages.push(`${sender}: ${text}`); }); const conversationText = messages.join('\n\n'); navigator.clipboard.writeText(conversationText).then(() => { window.Utils.showSuccess('对话已复制到剪贴板'); }).catch(() => { window.Utils.showError('复制失败'); }); }
    showConversationMenu(button) { const menuHtml = `<div class="dropdown-menu show"><a class="dropdown-item" href="#" onclick="chatPage.renameConversation('${$(button).closest('.conversation-item').data('id')}')"><i class="fas fa-edit"></i> 重命名</a><a class="dropdown-item" href="#" onclick="chatPage.deleteConversation('${$(button).closest('.conversation-item').data('id')}')"><i class="fas fa-trash"></i> 删除</a></div>`; $(button).append(menuHtml); $(document).one('click', () => { $('.dropdown-menu').remove(); }); }
    renameConversation(conversationId) { const newName = prompt('请输入新的对话名称：'); if (newName && newName.trim()) { window.Utils.showSuccess('重命名成功'); } }
    deleteConversation(conversationId) { if (confirm('确定要删除这个对话吗？')) { window.Utils.showSuccess('删除成功'); } }
    getWelcomeMessage() { return `<div class="message ai-message"><div class="message-avatar"><i class="fas fa-robot"></i></div><div class="message-content"><div class="message-text"><p>你好！我是基于知识图谱的智能问答助手。我可以帮助你：</p><ul><li>回答关于知识图谱中实体的问题</li><li>分析实体之间的关系</li><li>提供路径规划和推荐</li><li>进行概念解释和比较</li></ul><p>请直接输入你的问题，我会尽力为你提供准确的答案。</p></div><div class="message-time">${window.Utils.formatDate(new Date())}</div></div></div>`; }
    scrollToBottom() { const chatMessages = document.getElementById('chatMessages'); chatMessages.scrollTop = chatMessages.scrollHeight; }
    escapeHtml(text) { const div = document.createElement('div'); div.textContent = text; return div.innerHTML; }
}

let chatPage;
document.addEventListener('DOMContentLoaded', () => {
    chatPage = new ChatPage();
    window.chatPage = chatPage;
});