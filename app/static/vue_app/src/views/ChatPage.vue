<template>
  <div class="chat-container" :class="{ 'dark-theme': isDarkTheme }">
    <!-- 左侧边栏 -->
    <div class="sidebar" :class="{ collapsed: isSidebarCollapsed }">
      <div class="sidebar-header">
        <h1 class="app-title">教育问答 AI</h1>
        <div class="toggle-sidebar" @click="toggleSidebar">
          <i :class="isSidebarCollapsed ? 'el-icon-arrow-right' : 'el-icon-arrow-left'"></i>
        </div>
      </div>
      
      <!-- 新建聊天按钮 -->
      <div class="new-chat-btn" @click="createNewChat">
        <i class="el-icon-plus"></i>
        <span>开启新对话</span>
      </div>
      
      <!-- 对话历史 -->
      <div class="chat-history">
        <h3 class="history-title">最近对话</h3>
        <div class="clear-all" @click="clearAllChats">清除历史对话</div>
        
        <div 
          v-for="(chat, index) in chatHistory" 
          :key="index" 
          class="history-item"
          :class="{ 'active': currentChatIndex === index }"
          @click="selectChat(index)"
        >
          <i class="el-icon-chat-line-round"></i>
          <div class="chat-title-wrapper">
            <span class="chat-title">{{ chat.title }}</span>
          </div>
        </div>
      </div>
      
      <!-- 快捷功能按钮 -->
      <div class="quick-actions">
        <div class="quick-action-btn" @click="openGroupChat">
          <i class="el-icon-chat-dot-round"></i>
          <span v-show="!isSidebarCollapsed">群聊</span>
        </div>
        <div class="quick-action-btn" @click="openVideos">
          <i class="el-icon-video-camera"></i>
          <span v-show="!isSidebarCollapsed">{{ isTeacher ? '视频管理' : '视频学习' }}</span>
        </div>
        <div class="quick-action-btn" @click="openContentGenerator">
          <i class="el-icon-magic-stick"></i>
          <span v-show="!isSidebarCollapsed">内容生成</span>
        </div>
        <div v-if="isTeacher" class="quick-action-btn" @click="openTeacherAgent">
          <i class="el-icon-document-checked"></i>
          <span v-show="!isSidebarCollapsed">智能备课</span>
        </div>
        <div class="quick-action-btn" @click="openMindHelper">
          <i class="el-icon-star-off"></i>
          <span v-show="!isSidebarCollapsed">心灵助手</span>
        </div>
        <div class="quick-action-btn" @click="openGraphVisualizer">
          <i class="el-icon-share"></i>
          <span v-show="!isSidebarCollapsed">知识图谱</span>
        </div>
      </div>
      
      <!-- 底部设置 -->
      <div class="sidebar-footer">
        <div class="settings-container">
          <div class="settings-btn" @click="toggleSettingsMenu">
            <i class="el-icon-setting"></i>
            <span>设置</span>
          </div>
          
          <!-- 设置菜单 -->
          <transition name="fade">
            <div v-if="showSettingsMenu" class="settings-dropdown">
              <div class="settings-menu-item" @click="handleSettingsCommand('theme')">
                <i :class="isDarkTheme ? 'el-icon-moon-night' : 'el-icon-sunrise-1'"></i>
                <span>切换主题</span>
              </div>
              <div class="settings-divider"></div>
              <div class="settings-menu-item" @click="handleSettingsCommand('logout')">
                <i class="el-icon-switch-button"></i>
                <span>退出登录</span>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>
    
    <!-- 右侧聊天区域 -->
    <div class="chat-area">
      <!-- 消息列表 -->
      <div class="messages-container" ref="messagesContainer">
        <div v-if="!currentChat || currentChat.messages.length === 0" class="empty-chat">
          <div class="welcome-message">
            <h2>欢迎使用 AI 问答助手</h2>
            <p>开始提问以获取帮助</p>
          </div>
        </div>
        
        <div v-else>
          <div 
            v-for="(message, msgIndex) in currentChat.messages" 
            :key="msgIndex" 
            class="message"
            :class="{ 'user-message': message.role === 'user', 'ai-message': message.role === 'assistant' }"
          >
            <!-- AI消息布局 -->
            <template v-if="message.role === 'assistant'">
              <div class="message-avatar">
                <div class="ai-avatar">
                  <svg viewBox="0 0 32 32" width="24" height="24" fill="white">
                    <path d="M16,4C10.5,4,6,8.5,6,14c0,1.6,0.4,3.1,1.1,4.4c0.3,0.5,0.5,1.1,0.5,1.7v4.7c0,2,1.3,3.8,3.2,4.1c1.2,0.2,2.3-0.1,3.2-0.8c0.8-0.7,1.3-1.7,1.4-2.8l0.1-0.8c0-0.2,0.2-0.4,0.4-0.4c0,0,0,0,0.1,0c0.2,0,0.4,0.2,0.4,0.4l0.1,0.8c0.1,1.1,0.5,2.1,1.4,2.8c0.8,0.7,1.9,1,3.2,0.8c1.8-0.4,3.2-2.2,3.2-4.1V20c0-0.6,0.2-1.1,0.5-1.7C24.6,17.1,25,15.6,25,14C25,8.5,20.5,4,16,4z M14,18c-1.1,0-2-0.9-2-2s0.9-2,2-2s2,0.9,2,2S15.1,18,14,18z M18,18c-1.1,0-2-0.9-2-2s0.9-2,2-2s2,0.9,2,2S19.1,18,18,18z"></path>
                  </svg>
                </div>
              </div>
              <div class="message-content">
                <div class="message-text markdown-body" v-html="renderMarkdown(message.content)"></div>

                <!-- AI消息的操作按钮 -->
                <div class="message-actions">
                  <span 
                    class="action-btn" 
                    @click="generateVoice(message.content, msgIndex)" 
                    v-if="message.content" 
                    :class="{ 'generating': generatingVoiceForMessage === msgIndex }"
                    title="语音播报">
                    <i v-if="generatingVoiceForMessage !== msgIndex" class="el-icon-video-play"></i>
                    <i v-else class="el-icon-loading"></i>
                    <span v-if="generatingVoiceForMessage === msgIndex" class="generating-text">生成中...</span>
                  </span>
                  <span class="action-btn" @click="copyText(message.content)" title="复制">
                    <i class="el-icon-document-copy"></i>
                  </span>
                </div>
              </div>
            </template>
            
            <!-- 用户消息布局 -->
            <template v-else>
              <div class="message-content user-content">
                <div class="message-text">{{ message.content }}</div>
              </div>
              <div class="message-avatar">
                <div class="user-avatar">U</div>
              </div>
            </template>
          </div>
        </div>

        <!-- AI思考中的提示 -->
        <div v-if="isTyping" class="thinking-message">
          <div class="message-avatar">
            <div class="ai-avatar">
              <svg viewBox="0 0 32 32" width="24" height="24" fill="white">
                <path d="M16,4C10.5,4,6,8.5,6,14c0,1.6,0.4,3.1,1.1,4.4c0.3,0.5,0.5,1.1,0.5,1.7v4.7c0,2,1.3,3.8,3.2,4.1c1.2,0.2,2.3-0.1,3.2-0.8c0.8-0.7,1.3-1.7,1.4-2.8l0.1-0.8c0-0.2,0.2-0.4,0.4-0.4c0,0,0,0,0.1,0c0.2,0,0.4,0.2,0.4,0.4l0.1,0.8c0.1,1.1,0.5,2.1,1.4,2.8c0.8,0.7,1.9,1,3.2,0.8c1.8-0.4,3.2-2.2,3.2-4.1V20c0-0.6,0.2-1.1,0.5-1.7C24.6,17.1,25,15.6,25,14C25,8.5,20.5,4,16,4z M14,18c-1.1,0-2-0.9-2-2s0.9-2,2-2s2,0.9,2,2S15.1,18,14,18z M18,18c-1.1,0-2-0.9-2-2s0.9-2,2-2s2,0.9,2,2S19.1,18,18,18z"></path>
              </svg>
            </div>
          </div>
          <div class="message-content">
            <div class="thinking-animation">AI正在思考中<span></span><span></span><span></span></div>
          </div>
        </div>
      </div>
      
      <!-- 输入区域 -->
      <div class="input-container">
        <div class="input-box" :class="{ 'ai-typing': isTyping }">
          <div class="input-emoji">😊</div>
          <textarea 
            v-model="userInput" 
            @keydown.enter="handleEnterKey"
            placeholder="请输入您的问题..."
            ref="inputField"
            rows="3"
            :disabled="!isInputEnabled"
          ></textarea>
          <div class="send-btn" :class="{ 'disabled': !isInputEnabled }" @click="sendMessage">
            <i class="el-icon-s-promotion"></i>
          </div>
          <!-- 添加AI正在输入的提示 -->
          <div class="typing-indicator" v-if="!isInputEnabled">AI正在回复，请等待...</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import request from '@/utils/request'  // 导入配置好的 axios 实例
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'

// 配置 marked
marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang }).value
      } catch (err) {
        console.error(err)
      }
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
  gfm: true
})

export default {
  name: 'ChatPage',
  data() {
    return {
      isDarkTheme: false,
      userInput: '',
      isTyping: false,
      isInputEnabled: true,
      currentChatIndex: null,
      isSidebarCollapsed: false,
      chatHistory: [],
      ws: null,
      currentQuestionId: null,
      audioElement: null,
      welcomeMessageShown: false,
      generatingVoiceForMessage: null, // 跟踪正在生成语音的消息
      showSettingsMenu: false // 控制设置菜单显示
    }
  },
  computed: {
    currentChat() {
      return this.currentChatIndex !== null ? this.chatHistory[this.currentChatIndex] : null
    },
    token() {
      return localStorage.getItem('userToken') || localStorage.getItem('access_token')
    },
    isTeacher() {
      const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
      return userInfo.role && userInfo.role.toUpperCase() === 'TEACHER'
    }
  },
  methods: {
    toggleSettingsMenu() {
      this.showSettingsMenu = !this.showSettingsMenu
    },
    
    handleSettingsCommand(command) {
      this.showSettingsMenu = false // 关闭菜单
      if (command === 'theme') {
        this.toggleTheme()
      } else if (command === 'logout') {
        this.logout()
      }
    },
    
    toggleTheme() {
      this.isDarkTheme = !this.isDarkTheme
    },
    
    logout() {
      this.$confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        // 关闭 WebSocket 连接
        if (this.ws) {
          this.ws.close()
          this.ws = null
        }
        
        // 清除本地存储的所有认证相关数据
        localStorage.removeItem('userToken')
        localStorage.removeItem('access_token')
        localStorage.removeItem('userInfo')
        localStorage.removeItem('chatHistory')
        localStorage.removeItem('rememberMe')
        
        // 清除 sessionStorage
        sessionStorage.clear()
        
        // 提示退出成功
        this.$message.success('已退出登录')
        
        // 直接跳转到登录页并刷新，避免路由守卫问题
        window.location.href = '/login'
      }).catch(() => {
        // 用户取消退出
      })
    },
    
    toggleSidebar() {
      this.isSidebarCollapsed = !this.isSidebarCollapsed
    },
    
    createNewChat() {
      const existingEmptyChat = this.chatHistory.findIndex(chat => chat.messages.length === 0)
      
      if (existingEmptyChat !== -1) {
        this.currentChatIndex = existingEmptyChat
        this.$nextTick(() => {
          this.$refs.inputField.focus()
        })
        return
      }

      const newChat = {
        id: Date.now(),
        title: '新对话',
        messages: []
      }
      this.chatHistory.unshift(newChat)
      this.currentChatIndex = 0
      
      // 立即保存到 localStorage，防止跳转到群聊再返回时新对话丢失
      this.saveChatHistory()
      
      // 如果是第一次创建，显示欢迎消息
      if (!this.welcomeMessageShown) {
        this.showWelcomeMessage()
      }
      
      this.$nextTick(() => {
        this.$refs.inputField.focus()
      })
    },
    
    showWelcomeMessage() {
      if (this.welcomeMessageShown) return
      
      const welcomeMessage = `你好！我是基于知识图谱的智能问答助手。我可以帮助你：

• 回答关于知识图谱中实体的问题
• 分析实体之间的关系
• 提供路径规划和推荐
• 进行概念解释和比较

请告诉我你想了解什么？`

      if (this.currentChat) {
        this.currentChat.messages.push({
          role: 'assistant',
          content: welcomeMessage
        })
        
        this.welcomeMessageShown = true
        
        // 立即保存到 localStorage
        this.saveChatHistory()
        
        // 滚动到底部
        this.$nextTick(() => {
          if (this.$refs.messagesContainer) {
            this.$refs.messagesContainer.scrollTop = this.$refs.messagesContainer.scrollHeight
          }
        })
      }
    },
    
    selectChat(index) {
      this.currentChatIndex = index
      this.$nextTick(() => {
        if (this.$refs.messagesContainer) {
          this.$refs.messagesContainer.scrollTop = this.$refs.messagesContainer.scrollHeight
        }
      })
    },
    
    clearAllChats() {
      this.$confirm('确定要清除所有对话记录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.chatHistory = []
        this.currentChatIndex = null
        this.$message.success('清除成功!')
      }).catch(() => {})
    },
    
    openGroupChat() {
      this.$router.push('/group-chat')
    },
    
    openVideos() {
      // 根据用户角色跳转到对应的视频页面
      if (this.isTeacher) {
        this.$router.push('/teacher/videos')
      } else {
        this.$router.push('/student/videos')
      }
    },

    openContentGenerator() {
      if (this.isTeacher) {
        this.$router.push('/teacher/generate')
      } else {
        this.$router.push('/student/generate')
      }
    },

    openTeacherAgent() {
      this.$router.push('/teacher/agent')
    },
    
    openMindHelper() {
      const token = localStorage.getItem('userToken')
      if (token) {
        // 通过 nginx 代理路径 /mindhelper 访问心灵助手（ChatVRM）
        const mindHelperUrl = process.env.VUE_APP_MIND_ASSIST_URL || '/mindhelper'
        window.open(`${mindHelperUrl}?token=${token}`, '_blank')
      } else {
        this.$message.error('请先登录')
      }
    },
    
    openGraphVisualizer() {
      const token = localStorage.getItem('userToken')
      if (token) {
        window.open(`http://localhost:3000?token=${token}`, '_blank')
      } else {
        this.$message.error('请先登录')
      }
    },
    
    async sendMessage() {
      if (!this.userInput.trim() || !this.isInputEnabled) return
      
      if (!this.token) {
        this.$message.error('未登录，请先登录')
        this.$router.push('/login')
        return
      }
      
      // 如果没有当前聊天，创建一个新的
      if (this.currentChatIndex === null) {
        this.createNewChat()
      }
      
      const userContent = this.userInput.trim()
      
      // 添加用户消息
      this.currentChat.messages.push({
        role: 'user',
        content: userContent
      })
      
      // 更新聊天标题（如果是第一条消息）
      if (this.currentChat.messages.length === 1) {
        const firstLine = userContent.split('\n')[0]
        this.currentChat.title = firstLine.substring(0, 30) + (firstLine.length > 30 ? '...' : '')
      }
      
      this.userInput = ''
      
      // 滚动到底部
      this.$nextTick(() => {
        if (this.$refs.messagesContainer) {
          this.$refs.messagesContainer.scrollTop = this.$refs.messagesContainer.scrollHeight
        }
      })
      
      // 设置正在输入状态
      this.isTyping = true
      this.isInputEnabled = false
      
      // 通过 HTTP API 提交问题（这会创建后台任务）
      try {
        const response = await axios.post('/api/v1/questions', {
          text: userContent,
          force_regenerate: false
        }, {
          headers: {
            'Authorization': `Bearer ${this.token}`
          }
        })
        
        console.log('问题已提交:', response.data)
        this.currentQuestionId = response.data.question_id
      } catch (error) {
        console.error('提交问题失败:', error)
        
        // 检查是否是认证错误
        if (error.response && error.response.status === 401) {
          this.handleAuthError()
          return
        }
        
        this.$message.error('提交问题失败')
        this.isTyping = false
        this.isInputEnabled = true
      }
    },
    
    initWebSocket() {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        return
      }
      
      // 使用相对路径，通过 nginx 代理转发 WebSocket，避免硬编码端口
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/ws/qa?token=${this.token}`
      console.log('建立WebSocket连接:', wsUrl)
      
      this.ws = new WebSocket(wsUrl)
      
      this.ws.onopen = () => {
        console.log('WebSocket连接已建立')
      }
      
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        console.log('收到WebSocket消息:', data)
        
        switch (data.type) {
          case 'status':
            // 状态更新（保持"AI正在思考"状态）
            if (data.data && data.data.status) {
              console.log('AI状态:', data.data.status)
              // 继续显示思考中状态
              this.isTyping = true
            }
            break
            
          case 'answer':
            // 完整答案（后端返回的主要类型）
            console.log('收到完整答案')
            
            // 隐藏思考中状态
            this.isTyping = false
            this.isInputEnabled = true
            
            if (data.data && data.data.answer) {
              // 添加AI回复消息
              this.currentChat.messages.push({
                role: 'assistant',
                content: data.data.answer
              })
              
              // 保存 question_id
              if (data.question_id) {
                this.currentQuestionId = data.question_id
              }
              
              // 滚动到底部
              this.$nextTick(() => {
                if (this.$refs.messagesContainer) {
                  this.$refs.messagesContainer.scrollTop = this.$refs.messagesContainer.scrollHeight
                }
              })
              
              // 保存聊天历史到 localStorage
              this.saveChatHistory()
            }
            break
            
          case 'answer_stream':
            // 流式输出AI回复（首次收到时隐藏思考状态）
            if (this.isTyping) {
              this.isTyping = false
            }
            
            if (!this.currentChat.messages.length || this.currentChat.messages[this.currentChat.messages.length - 1].role !== 'assistant') {
              // 添加新的AI消息
              this.currentChat.messages.push({
                role: 'assistant',
                content: data.content || ''
              })
            } else {
              // 追加内容
              this.currentChat.messages[this.currentChat.messages.length - 1].content += (data.content || '')
            }
            
            // 滚动到底部
            this.$nextTick(() => {
              if (this.$refs.messagesContainer) {
                this.$refs.messagesContainer.scrollTop = this.$refs.messagesContainer.scrollHeight
              }
            })
            break
            
          case 'answer_complete':
            // 回复完成
            this.currentQuestionId = data.question_id
            this.isInputEnabled = true
            this.isTyping = false
            console.log('回复完成, question_id:', this.currentQuestionId)
            
            // 保存聊天历史
            this.saveChatHistory()
            break
            
          case 'error':
            // 错误消息
            this.$message.error(data.message || '发生错误')
            this.isTyping = false
            this.isInputEnabled = true
            break
            
          default:
            console.warn('未知的消息类型:', data.type)
        }
      }
      
      this.ws.onerror = (error) => {
        console.error('WebSocket错误:', error)
        this.$message.error('WebSocket连接失败，可能是认证失效')
        this.isTyping = false
        this.isInputEnabled = true
        
        // WebSocket连接失败，可能是token失效
        this.handleAuthError()
      }
      
      this.ws.onclose = (event) => {
        console.log('WebSocket连接已关闭, code:', event.code, 'reason:', event.reason)
        this.ws = null
        
        // 如果是异常关闭（非正常关闭码），可能是认证问题
        // 1000 是正常关闭，1001 是离开页面，1006 是异常关闭
        if (event.code === 1006 || event.code === 1008 || event.code === 1011) {
          console.warn('WebSocket异常关闭，可能是认证失效')
          this.handleAuthError()
        }
      }
    },
    
    async generateVoice(text, messageIndex) {
      if (!text) return
      
      // 如果已经在生成语音，不允许重复点击
      if (this.generatingVoiceForMessage !== null) {
        this.$message.warning('请等待当前语音生成完成')
        return
      }
      
      try {
        // 设置正在生成语音的消息索引
        this.generatingVoiceForMessage = messageIndex
        
        const formData = new FormData()
        formData.append('text', text)
        formData.append('voice_type', 'male')  // 使用男声（阿里云 CosyVoice API）
        
        // 调用后端 TTS API（已迁移至阿里云 CosyVoice）
        // 使用配置好的 request 实例,确保请求地址正确
        const response = await request.post('/api/v1/tts/stream', formData, {
          headers: {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'multipart/form-data'
          },
          responseType: 'blob',
          timeout: 60000, // 阿里云 CosyVoice API 响应较快，设置60秒超时
          onDownloadProgress: (progressEvent) => {
            // 可选：显示下载进度
            console.log('语音生成进度:', progressEvent.loaded)
          }
        })
        
        // 检查响应是否成功
        if (!response.data || response.data.size === 0) {
          throw new Error('服务器返回空的音频数据')
        }
        
        const audioBlob = response.data
        const audioUrl = URL.createObjectURL(audioBlob)
        
        // 停止之前的播放
        if (this.audioElement) {
          this.audioElement.pause()
          URL.revokeObjectURL(this.audioElement.src)
          this.audioElement = null
        }
        
        this.audioElement = new Audio(audioUrl)
        
        // 添加错误处理
        this.audioElement.onerror = (e) => {
          console.error('音频播放失败:', e)
          this.$message.error('音频播放失败')
          URL.revokeObjectURL(audioUrl)
        }
        
        this.audioElement.onended = () => {
          URL.revokeObjectURL(audioUrl)
        }
        
        await this.audioElement.play()
        this.$message.success('开始播放语音')
        
      } catch (error) {
        console.error('语音生成失败:', error)
        
        // 根据不同的错误类型提供更详细的错误信息
        if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
          this.$message.error('语音生成超时（ChatTTS CPU模式较慢，请耐心等待或尝试较短的文本）')
        } else if (error.response) {
          // 服务器返回了错误响应
          const status = error.response.status
          if (status === 504) {
            this.$message.error('服务器响应超时(504)，TTS服务可能未启动或响应缓慢')
          } else if (status === 502) {
            this.$message.error('网关错误(502)，TTS服务可能未启动')
          } else if (status === 500) {
            this.$message.error('服务器内部错误(500)，请联系管理员')
          } else if (status === 401) {
            this.handleAuthError()
            return
          } else {
            this.$message.error(`语音生成失败 (${status})`)
          }
        } else if (error.request) {
          // 请求已发送但没有收到响应
          this.$message.error('无法连接到TTS服务，请检查网络连接')
        } else {
          // 其他错误
          this.$message.error('语音生成失败: ' + (error.message || '未知错误'))
        }
      } finally {
        // 无论成功失败，都要清除生成状态
        this.generatingVoiceForMessage = null
      }
    },
    
    copyText(text) {
      navigator.clipboard.writeText(text).then(() => {
        this.$message.success('已复制到剪贴板')
      }).catch(() => {
        this.$message.error('复制失败')
      })
    },
    
    renderMarkdown(content) {
      return marked(content)
    },
    
    handleEnterKey(e) {
      // 如果按下了Shift键，不阻止默认行为，允许换行
      if (e.shiftKey) {
        return
      }
      
      // 如果只按下了Enter键，阻止默认行为并发送消息
      e.preventDefault()
      this.sendMessage()
    },
    
    saveChatHistory() {
      try {
        localStorage.setItem('chatHistory', JSON.stringify(this.chatHistory))
      } catch (e) {
        console.error('保存聊天历史失败:', e)
      }
    },
    
    handleAuthError() {
      // 防止重复弹窗和跳转
      if (this._authErrorHandled) {
        return
      }
      this._authErrorHandled = true
      
      // 清除本地存储的token
      localStorage.removeItem('userToken')
      localStorage.removeItem('access_token')
      
      // 显示提示并跳转到登录页
      this.$message.warning('登录已过期，请重新登录')
      
      setTimeout(() => {
        this.$router.push('/login')
      }, 1500)
    }
  },
  mounted() {
    // 检查登录状态
    if (!this.token) {
      this.$message.warning('未登录，即将跳转到登录页')
      setTimeout(() => {
        this.$router.push('/login')
      }, 2000)
      return
    }
    
    // 初始化 WebSocket
    this.initWebSocket()
    
    // 从localStorage加载历史记录
    const savedHistory = localStorage.getItem('chatHistory')
    if (savedHistory) {
      try {
        this.chatHistory = JSON.parse(savedHistory)
      } catch (e) {
        console.error('加载历史记录失败:', e)
      }
    }
    
    // 如果没有对话，创建一个新的并显示欢迎消息
    if (this.chatHistory.length === 0) {
      this.createNewChat()
    } else {
      this.currentChatIndex = 0
    }
  },
  beforeDestroy() {
    // 关闭 WebSocket
    if (this.ws) {
      this.ws.close()
    }
    
    // 停止音频播放
    if (this.audioElement) {
      this.audioElement.pause()
    }
  }
}
</script>

<style scoped>
/* 基础样式 */
.chat-container {
  display: flex;
  height: 100vh;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: #333;
  background-color: #f8f7fd;
  transition: all 0.3s ease;
}

/* 深色主题 */
.dark-theme {
  background-color: #1a1a1a;
  color: #f5f5f5;
}

.dark-theme .sidebar {
  background-color: #252525;
  border-right: 1px solid #333;
}

.dark-theme .chat-area {
  background-color: #1a1a1a;
}

.dark-theme .input-box {
  background-color: #333;
  border: 1px solid #444;
}

.dark-theme .input-box textarea {
  background-color: #333;
  color: #f5f5f5;
}

.dark-theme .message.user-message {
  background-color: transparent;
}

.dark-theme .message.ai-message {
  background-color: transparent;
}

.dark-theme .message.ai-message .message-content {
  background-color: #252525;
}

.dark-theme .new-chat-btn,
.dark-theme .history-item {
  background-color: #333;
  color: #f5f5f5;
}

.dark-theme .history-item:hover {
  background-color: #444;
}

.dark-theme .history-item.active {
  background-color: #4a4a4a;
}

.dark-theme .quick-actions {
  border-top: 1px solid #333;
  border-bottom: 1px solid #333;
}

.dark-theme .quick-action-btn {
  color: #bbb;
}

.dark-theme .quick-action-btn:not(:last-child) {
  border-bottom: 1px solid #333;
}

.dark-theme .quick-action-btn:hover {
  color: #409EFF;
}

.dark-theme .sidebar-footer {
  border-top: 1px solid #333;
}

.dark-theme .settings-btn {
  color: #bbb;
}

/* 侧边栏样式 */
.sidebar {
  width: 280px;
  background-color: #ffffff;
  border-right: 1px solid #e4dffd;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.3s ease;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar.collapsed .app-title, 
.sidebar.collapsed .chat-title,
.sidebar.collapsed .history-title,
.sidebar.collapsed .clear-all,
.sidebar.collapsed .settings-btn span,
.sidebar.collapsed .new-chat-btn span,
.sidebar.collapsed .quick-action-btn span {
  display: none;
}

.sidebar.collapsed .new-chat-btn,
.sidebar.collapsed .history-item,
.sidebar.collapsed .sidebar-footer,
.sidebar.collapsed .quick-action-btn {
  justify-content: center;
}

.sidebar.collapsed .sidebar-header {
  padding: 15px 10px;
}

.sidebar.collapsed .toggle-sidebar {
  margin: 0 auto;
}

.sidebar.collapsed .chat-history {
  padding: 0 5px;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e4dffd;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.app-title {
  font-size: 22px;
  font-weight: bold;
  margin: 0;
  color: #6c5dd3;
}

.new-chat-btn {
  margin: 12px;
  padding: 10px 15px;
  background: linear-gradient(135deg, #8b7fd6 0%, #9f8ce5 100%);
  color: white;
  border-radius: 25px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.new-chat-btn:hover {
  background: linear-gradient(135deg, #7d6ecc 0%, #8f7dd9 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 127, 214, 0.3);
}

.quick-actions {
  padding: 15px;
  border-top: 1px solid #e4dffd;
  border-bottom: 1px solid #e4dffd;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quick-action-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: #666;
  padding: 8px 0;
  transition: color 0.3s;
}

.quick-action-btn:not(:last-child) {
  border-bottom: 1px solid #e4dffd;
  padding-bottom: 12px;
  margin-bottom: 12px;
}

.quick-action-btn:hover {
  color: #8b7fd6;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px;
}

.history-title {
  font-size: 14px;
  color: #666;
  margin: 15px 0 10px;
  display: inline-block;
}

.clear-all {
  float: right;
  font-size: 12px;
  color: #8b7fd6;
  margin-top: 15px;
  cursor: pointer;
}

.history-item {
  padding: 10px 15px;
  margin: 5px 0;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: background-color 0.2s;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.history-item:hover {
  background-color: #f8f7fd;
}

.history-item.active {
  background: linear-gradient(90deg, #f0edfc 0%, #e4dffd 100%);
  border-left: 3px solid #8b7fd6;
}

.chat-title-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.chat-title {
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.sidebar-footer {
  padding: 15px;
  border-top: 1px solid #e4dffd;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.settings-container {
  position: relative;
}

.settings-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: #666;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.settings-btn:hover {
  background-color: #f5f5f5;
}

.dark-theme .settings-btn:hover {
  background-color: #333;
}

.settings-dropdown {
  position: absolute;
  bottom: 100%;
  left: 0;
  margin-bottom: 10px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  padding: 8px 0;
  min-width: 180px;
  z-index: 1000;
}

.dark-theme .settings-dropdown {
  background: #2c2c2c;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.5);
}

.settings-menu-item {
  padding: 10px 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: background-color 0.2s;
  color: #333;
}

.dark-theme .settings-menu-item {
  color: #ddd;
}

.settings-menu-item:hover {
  background-color: #f5f5f5;
}

.dark-theme .settings-menu-item:hover {
  background-color: #3a3a3a;
}

.settings-divider {
  height: 1px;
  background-color: #e8e8e8;
  margin: 5px 0;
}

.dark-theme .settings-divider {
  background-color: #444;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter, .fade-leave-to {
  opacity: 0;
}

.theme-toggle {
  cursor: pointer;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.theme-toggle:hover {
  background-color: #f8f7fd;
}

.toggle-sidebar {
  cursor: pointer;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.toggle-sidebar:hover {
  background-color: #f8f7fd;
}

.dark-theme .toggle-sidebar:hover {
  background-color: #444;
}

/* 聊天区域样式 */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.input-container,
.messages-container {
  padding-left: 20px;
  padding-right: 20px;
}

.input-container {
  padding-top: 15px;
  padding-bottom: 15px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding-top: 20px;
  padding-bottom: 20px;
  display: flex;
  flex-direction: column;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  scroll-behavior: smooth;
  height: calc(100vh - 120px);
}

.empty-chat {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #888;
}

.welcome-message {
  text-align: center;
}

.welcome-message h2 {
  font-size: 24px;
  margin-bottom: 10px;
}

.message {
  display: flex;
  margin-bottom: 20px;
  width: 100%;
}

.message-avatar {
  margin-right: 12px;
  min-width: 36px;
}

.user-message {
  justify-content: flex-end;
}

.ai-message {
  justify-content: flex-start;
}

.message-content  {
  font-size: 14px;
  max-width: 70%;
}

.user-message .message-content {
  max-width: max-content;
}

.ai-message .message-content {
  max-width: 70%;
}

.user-message .message-avatar {
  margin-right: 0;
  margin-left: 12px;
}

.user-content {
  text-align: left;
  background: linear-gradient(135deg, #8b7fd6 0%, #9f8ce5 100%) !important;
  color: white;
}

.user-content .message-text {
  font-size: 18px;
}

.user-avatar, .ai-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.user-avatar {
  background: linear-gradient(135deg, #8b7fd6 0%, #9f8ce5 100%);
  color: white;
}

.ai-avatar {
  background: linear-gradient(135deg, #7d6ecc 0%, #8f7dd9 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-content {
  flex: 1;
  padding: 15px;
  border-radius: 10px;
  position: relative;
}

.user-message .message-content {
  background-color: #f0f0f0;
}

.ai-message .message-content {
  background-color:rgb(226, 220, 251);
  border: 1px solid #e4dffd;
}

.message-text {
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 16px;
}

.message-actions {
  display: flex;
  gap: 15px;
  margin-top: 10px;
}

.action-btn {
  cursor: pointer;
  color: #777;
  transition: color 0.2s;
  display: flex;
  align-items: center;
  gap: 5px;
}

.action-btn:hover {
  color: #8b7fd6;
}

.action-btn.generating {
  color: #8b7fd6;
  cursor: wait;
  pointer-events: none;
}

.action-btn .generating-text {
  font-size: 12px;
  margin-left: 3px;
}

.action-btn .el-icon-loading {
  animation: rotating 1s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 输入区域样式 */
.input-box {
  display: flex;
  align-items: flex-start;
  background-color: #fff;
  border: 2px solid #e4dffd;
  border-radius: 20px;
  padding: 10px 15px;
  position: relative;
  transition: all 0.3s ease;
}

.input-box:focus-within {
  border-color: #8b7fd6;
  box-shadow: 0 0 0 3px rgba(139, 127, 214, 0.1);
}

.input-box.ai-typing {
  border-color: #ddd;
  background-color: #f9f9f9;
  opacity: 0.9;
}

.typing-indicator {
  position: absolute;
  top: -30px;
  left: 15px;
  font-size: 12px;
  color: #ff6b6b;
  background-color: #fff8f8;
  padding: 5px 10px;
  border-radius: 10px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  animation: pulse 1.5s infinite;
  z-index: 10;
}

@keyframes pulse {
  0% { opacity: 0.6; }
  50% { opacity: 1; }
  100% { opacity: 0.6; }
}

.dark-theme .typing-indicator {
  background-color: #3a3a3a;
  color: #ff8080;
}

.input-emoji {
  font-size: 18px;
  margin-right: 10px;
  cursor: pointer;
  padding-top: 5px;
  opacity: 1;
  transition: opacity 0.3s ease;
}

.ai-typing .input-emoji {
  opacity: 0.5;
}

.input-box textarea {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  resize: none;
  height: 72px;
  min-height: 72px;
  font-family: inherit;
  font-size: 14px;
  padding: 5px 0;
  line-height: 1.5;
  transition: all 0.3s ease;
}

.input-box textarea:disabled {
  color: #999;
  cursor: not-allowed;
  background-color: transparent;
  opacity: 0.8;
}

.dark-theme .input-box textarea:disabled {
  background-color: transparent;
  color: #777;
}

.send-btn {
  cursor: pointer;
  margin-left: 10px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b7fd6 0%, #9f8ce5 100%);
  color: white;
  transition: all 0.3s ease;
  margin-top: 5px;
}

.send-btn.disabled {
  background: #d0d0d0;
  cursor: not-allowed;
  opacity: 0.7;
}

.dark-theme .send-btn.disabled {
  background-color: #444;
  opacity: 0.7;
}

.send-btn:hover:not(.disabled) {
  background: linear-gradient(135deg, #7d6ecc 0%, #8f7dd9 100%);
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(139, 127, 214, 0.3);
}

/* 思考中消息样式 */
.thinking-message {
  display: flex;
  margin-bottom: 20px;
  width: 100%;
  justify-content: flex-start;
  opacity: 0.8;
}

.thinking-message .message-content {
  background-color: #f9f9f9;
  padding: 15px;
  border-radius: 10px;
  position: relative;
}

.dark-theme .thinking-message .message-content {
  background-color: #252525;
}

.thinking-animation {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #666;
  font-size: 14px;
}

.thinking-animation span {
  width: 4px;
  height: 4px;
  background-color: #666;
  border-radius: 50%;
  display: inline-block;
}

.thinking-animation span:nth-child(1) {
  animation: thinking 1.4s infinite;
}

.thinking-animation span:nth-child(2) {
  animation: thinking 1.4s infinite 0.2s;
}

.thinking-animation span:nth-child(3) {
  animation: thinking 1.4s infinite 0.4s;
}

@keyframes thinking {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
}

.dark-theme .thinking-animation {
  color: #999;
}

.dark-theme .thinking-animation span {
  background-color: #999;
}

/* Markdown样式 */
.markdown-body >>> p {
  margin-top: 0em;
  margin-bottom: 0.5em;
}

.markdown-body >>> h1,
.markdown-body >>> h2,
.markdown-body >>> h3 {
  margin-top: 0.5em;
  margin-bottom: 0.3em;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-body >>> pre {
  padding: 0.8em;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #282c34;
  border-radius: 6px;
  margin: 0.5em 0;
}

.markdown-body >>> code {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(27, 31, 35, 0.05);
  border-radius: 3px;
}

.markdown-body >>> pre > code {
  padding: 0;
  margin: 0;
  font-size: 100%;
  word-break: normal;
  white-space: pre;
  background: transparent;
  border: 0;
}
</style>
