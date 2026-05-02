<template>
  <div class="generator-container" :class="{ 'dark-theme': isDarkTheme }">
    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ collapsed: isSidebarCollapsed }">
      <div class="sidebar-header">
        <h1 class="app-title">✨ 内容生成</h1>
        <div class="toggle-sidebar" @click="toggleSidebar">
          <i :class="isSidebarCollapsed ? 'el-icon-arrow-right' : 'el-icon-arrow-left'"></i>
        </div>
      </div>

      <!-- 生成按钮 -->
      <div class="new-generate-btn" @click="generate" :class="{ loading: generating }">
        <i :class="generating ? 'el-icon-loading' : 'el-icon-magic-stick'"></i>
        <span>{{ generating ? '生成中...' : '立即生成' }}</span>
      </div>

      <!-- 配置区 -->
      <div class="filter-section">
        <h3 class="filter-title">内容类型</h3>
        <div
          v-for="type in contentTypes"
          :key="type.value"
          class="filter-item"
          :class="{ active: contentType === type.value }"
          @click="contentType = type.value"
        >
          <span class="type-emoji">{{ type.icon }}</span>
          <span>{{ type.label }}</span>
        </div>

        <h3 class="filter-title" style="margin-top:20px">难度级别</h3>
        <div
          v-for="d in difficulties"
          :key="d.value"
          class="filter-item"
          :class="{ active: difficulty === d.value }"
          @click="difficulty = d.value"
        >
          <i :class="d.icon"></i>
          <span>{{ d.label }}</span>
        </div>

        <h3 class="filter-title" style="margin-top:20px">知识点</h3>
        <div class="knowledge-input-wrap">
          <el-input
            v-model="knowledgePoint"
            type="textarea"
            :rows="5"
            placeholder="输入知识点，例如：\n二叉树的前中后序遍历\nHTTP与HTTPS的区别\nTCP三次握手过程"
            :disabled="generating"
            class="knowledge-textarea"
          />
        </div>

        <h3 class="filter-title" style="margin-top:16px">快捷示例</h3>
        <div
          v-for="ex in examples"
          :key="ex"
          class="filter-item example-item"
          @click="knowledgePoint = ex"
        >
          <i class="el-icon-arrow-right"></i>
          <span>{{ ex }}</span>
        </div>
      </div>

      <!-- 底部操作 -->
      <div class="sidebar-footer">
        <div v-if="generatedCode" class="footer-actions">
          <div class="action-btn" @click="copyCode">
            <i class="el-icon-copy-document"></i>
            <span>复制代码</span>
          </div>
          <div class="action-btn" @click="downloadHtml">
            <i class="el-icon-download"></i>
            <span>下载 HTML</span>
          </div>
        </div>
        <div class="settings-btn" @click="$router.push('/chat')">
          <i class="el-icon-back"></i>
          <span>返回聊天</span>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 顶部工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <span class="toolbar-title">{{ currentTitle }}</span>
          <el-tag v-if="contentType" size="small" type="info" style="margin-left:8px">
            {{ contentTypes.find(t => t.value === contentType).label }}
          </el-tag>
          <el-tag v-if="generatedCode" size="small" type="success" style="margin-left:4px">
            生成完成
          </el-tag>
        </div>
        <div class="toolbar-right" v-if="generatedCode">
          <el-button size="small" icon="el-icon-refresh" @click="refreshPreview">刷新预览</el-button>
          <el-button size="small" icon="el-icon-full-screen" @click="fullscreenVisible = true">全屏</el-button>
          <el-button size="small" type="primary" icon="el-icon-magic-stick" @click="generate">重新生成</el-button>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="!generatedCode && !generating" class="empty-state">
        <div class="empty-icon">✨</div>
        <p class="empty-title">AI 互动内容生成器</p>
        <p class="empty-sub">在左侧选择内容类型，输入知识点，点击「立即生成」</p>
        <div class="feature-cards">
          <div class="feature-card" v-for="type in contentTypes" :key="type.value" @click="contentType = type.value">
            <div class="feature-icon">{{ type.icon }}</div>
            <div class="feature-name">{{ type.label }}</div>
            <div class="feature-desc">{{ type.desc }}</div>
          </div>
        </div>
      </div>

      <!-- 生成中动画 -->
      <div v-if="generating" class="generating-state">
        <div class="pulse-ring"></div>
        <div class="generating-dots">
          <div class="gdot"></div>
          <div class="gdot"></div>
          <div class="gdot"></div>
        </div>
        <p class="gen-title">AI 正在创作互动内容</p>
        <p class="gen-sub">正在为「{{ knowledgePoint.slice(0, 20) }}」生成{{ contentTypes.find(t=>t.value===contentType).label }}...</p>
        <div class="progress-wrap">
          <div class="progress-bar" :style="{ width: streamProgress + '%' }"></div>
        </div>
        <span class="progress-text">{{ streamProgress }}%</span>
      </div>

      <!-- iframe 沙盒预览 -->
      <div v-if="generatedCode" class="preview-wrap">
        <iframe
          ref="previewFrame"
          class="preview-iframe"
          sandbox="allow-scripts"
          :srcdoc="generatedCode"
        ></iframe>
      </div>
    </div>

    <!-- 全屏对话框 -->
    <el-dialog
      :visible.sync="fullscreenVisible"
      title="全屏预览"
      fullscreen
      :append-to-body="true"
    >
      <iframe
        v-if="fullscreenVisible"
        class="fullscreen-iframe"
        sandbox="allow-scripts"
        :srcdoc="generatedCode"
      ></iframe>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'ContentGenerator',
  data() {
    return {
      isDarkTheme: false,
      isSidebarCollapsed: false,
      knowledgePoint: '',
      contentType: 'quiz',
      difficulty: 'medium',
      generating: false,
      generatedCode: '',
      streamBuffer: '',
      streamProgress: 0,
      fullscreenVisible: false,
      contentTypes: [
        { value: 'quiz', icon: '📝', label: '知识测验', desc: '选择题互动答题，即时反馈' },
        { value: 'animation', icon: '🎬', label: '动画演示', desc: '步骤可视化，逐帧讲解' },
        { value: 'game', icon: '🎮', label: '互动游戏', desc: '趣味小游戏，寓教于乐' }
      ],
      difficulties: [
        { value: 'easy', label: '简单', icon: 'el-icon-star-off' },
        { value: 'medium', label: '中等', icon: 'el-icon-star-on' },
        { value: 'hard', label: '困难', icon: 'el-icon-trophy' }
      ],
      examples: [
        '二叉树的三种遍历方式',
        'TCP三次握手过程',
        'HTTP与HTTPS的区别',
        '冒泡排序算法',
        'Python装饰器原理'
      ]
    }
  },
  computed: {
    currentTitle() {
      if (!this.generatedCode && !this.generating) return '请在左侧配置并生成内容'
      if (this.generating) return '正在生成...'
      return this.knowledgePoint.slice(0, 30) || '生成完成'
    }
  },
  methods: {
    toggleSidebar() {
      this.isSidebarCollapsed = !this.isSidebarCollapsed
    },
    async generate() {
      if (!this.knowledgePoint.trim()) {
        this.$message.warning('请输入知识点描述')
        return
      }
      this.generating = true
      this.generatedCode = ''
      this.streamBuffer = ''
      this.streamProgress = 0
      const token = localStorage.getItem('userToken')
      try {
        const response = await fetch('/api/v1/generate/interactive', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            knowledge_point: this.knowledgePoint,
            content_type: this.contentType,
            difficulty: this.difficulty
          })
        })
        if (!response.ok) {
          const err = await response.json()
          throw new Error(err.detail || '请求失败')
        }
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let totalChunks = 0
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const text = decoder.decode(value, { stream: true })
          const lines = text.split('\n')
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const data = line.slice(6)
            if (data === '[DONE]') {
              this.generatedCode = this.cleanHtml(this.streamBuffer)
              this.streamProgress = 100
              this.$message.success('互动内容生成完成！')
              break
            }
            if (data.startsWith('[ERROR]')) throw new Error(data.replace('[ERROR] ', ''))
            this.streamBuffer += data.replace(/\\n/g, '\n')
            totalChunks++
            this.streamProgress = Math.min(90, Math.floor(totalChunks * 1.5))
          }
        }
      } catch (error) {
        this.$message.error('生成失败：' + error.message)
      } finally {
        this.generating = false
      }
    },
    cleanHtml(raw) {
      let code = raw.trim()
      const match = code.match(/```(?:html)?\s*([\s\S]*?)```/)
      if (match) code = match[1].trim()
      return code
    },
    refreshPreview() {
      if (this.$refs.previewFrame) {
        const code = this.generatedCode
        this.$refs.previewFrame.srcdoc = ''
        this.$nextTick(() => { this.$refs.previewFrame.srcdoc = code })
      }
    },
    copyCode() {
      navigator.clipboard.writeText(this.generatedCode)
        .then(() => this.$message.success('代码已复制到剪贴板'))
        .catch(() => {
          const el = document.createElement('textarea')
          el.value = this.generatedCode
          document.body.appendChild(el)
          el.select()
          document.execCommand('copy')
          document.body.removeChild(el)
          this.$message.success('代码已复制')
        })
    },
    downloadHtml() {
      const blob = new Blob([this.generatedCode], { type: 'text/html;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${this.knowledgePoint.slice(0, 20)}_${this.contentType}.html`
      a.click()
      URL.revokeObjectURL(url)
    }
  }
}
</script>

<style scoped>
.generator-container {
  display: flex;
  height: 100vh;
  background: #f8f7fd;
}

/* ===== 侧边栏（与TeacherVideos保持一致） ===== */
.sidebar {
  width: 280px;
  background: white;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  overflow: hidden;
}
.sidebar.collapsed { width: 60px; }

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.app-title {
  font-size: 20px;
  font-weight: 700;
  color: #6c5ce7;
  margin: 0;
  white-space: nowrap;
}
.sidebar.collapsed .app-title { display: none; }

.toggle-sidebar {
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: background 0.2s;
  flex-shrink: 0;
}
.toggle-sidebar:hover { background: #f0f0f0; }

/* 生成按钮 */
.new-generate-btn {
  margin: 20px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
  color: white;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
  transition: transform 0.2s, opacity 0.2s;
  white-space: nowrap;
}
.new-generate-btn:hover { transform: translateY(-2px); }
.new-generate-btn.loading { opacity: 0.7; cursor: not-allowed; }
.sidebar.collapsed .new-generate-btn span { display: none; }

/* 筛选区 */
.filter-section {
  padding: 0 20px;
  flex: 1;
  overflow-y: auto;
}
.sidebar.collapsed .filter-section { display: none; }

.filter-title {
  font-size: 12px;
  color: #999;
  text-transform: uppercase;
  margin: 20px 0 12px 0;
  letter-spacing: 1px;
}

.filter-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
  transition: all 0.2s;
  font-size: 14px;
  color: #555;
}
.filter-item:hover { background: #f8f7fd; }
.filter-item.active {
  background: #f0edff;
  color: #6c5ce7;
  font-weight: 600;
}
.type-emoji { font-size: 16px; }

.example-item { font-size: 13px; color: #888; }
.example-item:hover { color: #6c5ce7; }

.knowledge-input-wrap { margin-top: 4px; }

/* 底部 */
.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid #e0e0e0;
}
.sidebar.collapsed .sidebar-footer .footer-actions { display: none; }
.sidebar.collapsed .sidebar-footer span { display: none; }

.footer-actions {
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.action-btn {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #555;
  transition: background 0.2s;
}
.action-btn:hover { background: #f8f7fd; color: #6c5ce7; }

.settings-btn {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: background 0.2s;
  font-size: 14px;
  color: #555;
}
.settings-btn:hover { background: #f8f7fd; }

/* ===== 主内容区 ===== */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.toolbar-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}
.toolbar-right { display: flex; gap: 8px; }

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 12px;
}
.empty-icon { font-size: 72px; }
.empty-title { font-size: 22px; font-weight: 700; color: #333; margin: 0; }
.empty-sub { font-size: 14px; color: #999; margin: 0; }

.feature-cards {
  display: flex;
  gap: 16px;
  margin-top: 24px;
  flex-wrap: wrap;
  justify-content: center;
}
.feature-card {
  background: white;
  border-radius: 12px;
  padding: 24px 20px;
  width: 180px;
  text-align: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: all 0.2s;
  border: 2px solid transparent;
}
.feature-card:hover {
  transform: translateY(-4px);
  border-color: #6c5ce7;
  box-shadow: 0 4px 16px rgba(108,92,231,0.2);
}
.feature-icon { font-size: 36px; margin-bottom: 8px; }
.feature-name { font-size: 15px; font-weight: 600; color: #333; margin-bottom: 6px; }
.feature-desc { font-size: 12px; color: #999; }

/* 生成中状态 */
.generating-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 40px;
}
.gen-title { font-size: 18px; font-weight: 600; color: #6c5ce7; margin: 0; }
.gen-sub { font-size: 14px; color: #999; margin: 0; }

.pulse-ring {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 4px solid #6c5ce7;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
  0% { transform: scale(0.8); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.6; }
  100% { transform: scale(0.8); opacity: 1; }
}

.generating-dots {
  display: flex;
  gap: 8px;
}
.gdot {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: #6c5ce7;
  animation: gdotbounce 1.2s infinite;
}
.gdot:nth-child(2) { animation-delay: 0.2s; }
.gdot:nth-child(3) { animation-delay: 0.4s; }
@keyframes gdotbounce {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
  40% { transform: scale(1.2); opacity: 1; }
}

.progress-wrap {
  width: 300px;
  height: 6px;
  background: #e8e4f8;
  border-radius: 3px;
  overflow: hidden;
}
.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #6c5ce7, #a29bfe);
  border-radius: 3px;
  transition: width 0.3s ease;
}
.progress-text { font-size: 13px; color: #999; }

/* 预览 */
.preview-wrap {
  flex: 1;
  overflow: hidden;
  padding: 20px 24px;
  background: #f8f7fd;
}
.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  background: white;
}
.fullscreen-iframe {
  width: 100%;
  height: calc(100vh - 55px);
  border: none;
}

/* 深色主题 */
.dark-theme { background: #1a1a1a; }
.dark-theme .sidebar { background: #252525; border-right-color: #333; }
.dark-theme .app-title { color: #a29bfe; }
.dark-theme .main-content { background: #1a1a1a; }
.dark-theme .toolbar { background: #252525; border-bottom-color: #333; }
.dark-theme .toolbar-title { color: #f5f5f5; }
.dark-theme .feature-card { background: #2a2a2a; }
.dark-theme .feature-name { color: #f5f5f5; }

/* 响应式 */
@media (max-width: 768px) {
  .sidebar { position: fixed; left: 0; top: 0; bottom: 0; z-index: 100; transform: translateX(-100%); }
  .sidebar:not(.collapsed) { transform: translateX(0); }
  .feature-cards { flex-direction: column; align-items: center; }
}
</style>
