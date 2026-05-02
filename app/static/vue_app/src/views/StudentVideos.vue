<template>
  <div class="student-videos-container" :class="{ 'dark-theme': isDarkTheme }">
    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ collapsed: isSidebarCollapsed }">
      <div class="sidebar-header">
        <h1 class="app-title">📚 视频学习</h1>
        <div class="toggle-sidebar" @click="toggleSidebar">
          <i :class="isSidebarCollapsed ? 'el-icon-arrow-right' : 'el-icon-arrow-left'"></i>
        </div>
      </div>
      
      <!-- 学习统计 -->
      <div class="stats-section">
        <div class="stat-item">
          <i class="el-icon-video-camera"></i>
          <div>
            <div class="stat-value">{{ totalVideos }}</div>
            <div class="stat-label">可学习视频</div>
          </div>
        </div>
        <div class="stat-item">
          <i class="el-icon-check"></i>
          <div>
            <div class="stat-value">{{ completedVideos }}</div>
            <div class="stat-label">已完成</div>
          </div>
        </div>
      </div>
      
      <!-- 筛选选项 -->
      <div class="filter-section">
        <h3 class="filter-title">筛选</h3>
        <div class="filter-item" 
             :class="{ active: currentFilter === 'all' }"
             @click="currentFilter = 'all'">
          <i class="el-icon-folder"></i>
          <span>全部视频</span>
        </div>
        <div class="filter-item"
             :class="{ active: currentFilter === 'in-progress' }"
             @click="currentFilter = 'in-progress'">
          <i class="el-icon-video-play"></i>
          <span>学习中</span>
        </div>
        <div class="filter-item"
             :class="{ active: currentFilter === 'completed' }"
             @click="currentFilter = 'completed'">
          <i class="el-icon-circle-check"></i>
          <span>已完成</span>
        </div>
        <div class="filter-item"
             :class="{ active: currentFilter === 'not-started' }"
             @click="currentFilter = 'not-started'">
          <i class="el-icon-circle-plus"></i>
          <span>未开始</span>
        </div>
      </div>
      
      <!-- 课程筛选 -->
      <div class="filter-section">
        <h3 class="filter-title">按课程筛选</h3>
        <div 
          class="filter-item"
          :class="{ active: currentCourse === null }"
          @click="currentCourse = null"
        >
          <i class="el-icon-folder"></i>
          <span>全部课程</span>
        </div>
        <div 
          v-for="course in courses"
          :key="course.id"
          class="filter-item"
          :class="{ active: currentCourse === course.id }"
          @click="selectCourse(course.id)"
        >
          <i class="el-icon-folder-opened"></i>
          <span>{{ course.name }}</span>
          <span class="count" v-if="course.video_count">{{ course.video_count }}</span>
        </div>
      </div>
      
      <!-- 底部设置 -->
      <div class="sidebar-footer">
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
        <div class="search-box">
          <el-input 
            v-model="searchQuery" 
            placeholder="搜索视频..."
            prefix-icon="el-icon-search"
            clearable
          ></el-input>
        </div>
      </div>
      
      <!-- 视频列表 -->
      <div v-if="loading" class="loading-container">
        <i class="el-icon-loading"></i>
        <p>加载中...</p>
      </div>
      
      <div v-else-if="filteredVideos.length === 0" class="empty-state">
        <i class="el-icon-video-camera"></i>
        <p>{{ emptyStateText }}</p>
      </div>
      
      <div v-else class="videos-grid">
        <video-card
          v-for="video in filteredVideos"
          :key="video.id"
          :video="video"
          :is-teacher="false"
          :progress="getVideoProgress(video.id)"
          :completed="isVideoCompleted(video)"
          @play="playVideo"
        />
      </div>
      
      <!-- 分页 -->
      <div v-if="totalPages > 1" class="pagination">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :total="totalCount"
          layout="prev, pager, next"
          @current-change="handlePageChange"
        ></el-pagination>
      </div>
    </div>
  </div>
</template>

<script>
import VideoCard from '@/components/VideoCard.vue'
import videosApi from '@/api/videos'
import coursesApi from '@/api/courses'

export default {
  name: 'StudentVideos',
  components: {
    VideoCard
  },
  data() {
    return {
      isDarkTheme: false,
      isSidebarCollapsed: false,
      loading: false,
      searchQuery: '',
      currentFilter: 'all',
      currentCourse: null,
      courses: [],
      videos: [],
      progressMap: {}, // videoId -> progress percentage
      currentPage: 1,
      pageSize: 12,
      totalCount: 0
    }
  },
  computed: {
    filteredVideos() {
      let filtered = this.videos
      
      // 按进度筛选
      if (this.currentFilter === 'completed') {
        filtered = filtered.filter(v => this.isVideoCompleted(v))
      } else if (this.currentFilter === 'in-progress') {
        filtered = filtered.filter(v => {
          const progress = this.getVideoProgress(v.id)
          return progress > 0 && !this.isVideoCompleted(v)
        })
      } else if (this.currentFilter === 'not-started') {
        filtered = filtered.filter(v => this.getVideoProgress(v.id) === 0)
      }
      
      // 按搜索词筛选
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        filtered = filtered.filter(v => 
          v.title.toLowerCase().includes(query) ||
          (v.description && v.description.toLowerCase().includes(query))
        )
      }
      
      return filtered
    },
    totalPages() {
      return Math.ceil(this.totalCount / this.pageSize)
    },
    totalVideos() {
      return this.videos.length
    },
    completedVideos() {
      return this.videos.filter(v => this.isVideoCompleted(v)).length
    },
    emptyStateText() {
      if (this.currentFilter === 'all') {
        return '暂无可学习的视频'
      } else if (this.currentFilter === 'completed') {
        return '还没有完成任何视频'
      } else if (this.currentFilter === 'in-progress') {
        return '还没有正在学习的视频'
      } else {
        return '所有视频都已开始学习'
      }
    }
  },
  mounted() {
    this.loadCourses()
    this.loadVideos()
    // loadProgress will be called automatically after loadVideos completes
  },
  activated() {
    this.loadVideos()
    // loadProgress will be called automatically after loadVideos completes
  },
  methods: {
    async loadCourses() {
      try {
        const response = await coursesApi.getPublishedCourses()
        this.courses = response || []
      } catch (error) {
        console.error('加载课程失败:', error)
      }
    },
    
    selectCourse(courseId) {
      this.currentCourse = courseId
      this.currentPage = 1
      this.loadVideos()
    },
    
    async loadVideos() {
      this.loading = true
      try {
        const params = {
          page: this.currentPage,
          page_size: this.pageSize
        }
        
        let response
        if (this.currentCourse) {
          // 加载指定课程的视频
          response = await coursesApi.getCourseDetail(this.currentCourse)
          this.videos = response.videos || []
          this.totalCount = this.videos.length
        } else {
          // 加载所有视频
          response = await videosApi.getAvailableVideos(params)
          this.videos = response.videos || []
          this.totalCount = response.total || this.videos.length
        }
        
        // 调试：输出API返回的原始数据
        console.log('=== loadVideos: API Response ===')
        console.log('Total videos:', this.videos.length)
        this.videos.forEach(v => {
          if (v.watch_progress) {
            console.log(`Video ${v.id} "${v.title}":`, {
              progress_seconds: v.watch_progress.progress_seconds,
              completed: v.watch_progress.completed,
              duration: v.duration
            })
          }
        })
        
      } catch (error) {
        console.error('加载视频失败:', error)
        this.$message.error('加载视频列表失败')
      } finally {
        this.loading = false
        // Load progress after videos are fetched
        await this.loadProgress()
      }
    },
    
    handlePageChange(page) {
      this.currentPage = page
      this.loadVideos()
    },
    
    async loadProgress() {
      // Extract progress from videos and populate progressMap
      // IMPORTANT: Keep the full watch_progress object for completed status
      this.progressMap = {}
      for (const video of this.videos) {
        if (video.watch_progress) {
          const progress = video.watch_progress
          if (video.duration && video.duration > 0) {
            const percentage = Math.min(100, Math.round((progress.progress_seconds / video.duration) * 100))
            this.progressMap[video.id] = percentage
          } else {
            this.progressMap[video.id] = 0
          }
          
          // Store the watch_progress object on the video for completed check
          // This ensures isVideoCompleted can access the completed field
          video._watch_progress_cached = progress
        } else {
          this.progressMap[video.id] = 0
          video._watch_progress_cached = null
        }
      }
      
      console.log('Progress loaded:', this.progressMap)
      console.log('Videos with watch_progress:', this.videos.filter(v => v._watch_progress_cached).map(v => ({
        id: v.id,
        title: v.title,
        completed: v._watch_progress_cached?.completed,
        progress_seconds: v._watch_progress_cached?.progress_seconds
      })))
      
      // 详细调试每个视频的completed状态
      console.log('\n=== 详细completed字段检查 ===')
      this.videos.forEach(v => {
        const cached = v._watch_progress_cached || v.watch_progress
        if (cached) {
          console.log(`\n视频 ${v.id} "${v.title}":`)
          console.log('  completed值:', cached.completed)
          console.log('  completed类型:', typeof cached.completed)
          console.log('  completed === true:', cached.completed === true)
          console.log('  progress_seconds:', cached.progress_seconds)
          console.log('  duration:', v.duration)
          console.log('  进度百分比:', this.progressMap[v.id] + '%')
        }
      })
    },
    
    isVideoCompleted(video) {
      // First check the cached watch_progress object for completed field
      const cachedProgress = video._watch_progress_cached || video.watch_progress
      
      if (cachedProgress) {
        // Debug logging (can be removed after testing)
        if (cachedProgress.completed) {
          console.log(`✅ Video ${video.id} "${video.title}" is COMPLETED (completed=true)`)
        }
        
        // Primary check: use the completed field from backend
        if (cachedProgress.completed === true) {
          return true
        }
      }
      
      // Fallback check: calculate from progress percentage
      const progress = this.getVideoProgress(video.id)
      const isCompleted = progress >= 95
      
      if (isCompleted) {
        console.log(`✅ Video ${video.id} "${video.title}" is COMPLETED (progress=${progress}%)`)
      }
      
      return isCompleted
    },
    
    getVideoProgress(videoId) {
      return this.progressMap[videoId] || 0
    },
    
    playVideo(video) {
      this.$router.push({
        name: 'VideoPlayer',
        params: { id: video.id }
      })
    },
    
    toggleSidebar() {
      this.isSidebarCollapsed = !this.isSidebarCollapsed
    }
  }
}
</script>

<style scoped>
.student-videos-container {
  display: flex;
  height: 100vh;
  background: #f8f7fd;
}

/* 侧边栏样式 */
.sidebar {
  width: 280px;
  background: white;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
}

.sidebar.collapsed {
  width: 60px;
}

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
}

.sidebar.collapsed .app-title {
  display: none;
}

.toggle-sidebar {
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.toggle-sidebar:hover {
  background: #f0f0f0;
}

.stats-section {
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8f7fd;
  border-radius: 8px;
  margin-bottom: 12px;
}

.stat-item:last-child {
  margin-bottom: 0;
}

.stat-item i {
  font-size: 24px;
  color: #6c5ce7;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #333;
}

.stat-label {
  font-size: 12px;
  color: #999;
}

.sidebar.collapsed .stats-section {
  display: none;
}

.filter-section {
  padding: 0 20px;
  flex: 1;
  overflow-y: auto;
}

.filter-title {
  font-size: 12px;
  color: #999;
  text-transform: uppercase;
  margin: 20px 0 12px 0;
}

.filter-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
  transition: all 0.2s;
}

.filter-item:hover {
  background: #f8f7fd;
}

.filter-item.active {
  background: #f0edff;
  color: #6c5ce7;
  font-weight: 600;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid #e0e0e0;
}

.settings-btn {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: background 0.2s;
}

.settings-btn:hover {
  background: #f8f7fd;
}

/* 主内容区 */
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.search-box {
  flex: 1;
  max-width: 400px;
}

.loading-container {
  text-align: center;
  padding: 60px 20px;
  color: #999;
  font-size: 32px;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-state i {
  font-size: 80px;
  color: #ddd;
  margin-bottom: 20px;
}

.empty-state p {
  font-size: 16px;
  color: #999;
}

.videos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.pagination {
  margin-top: 40px;
  display: flex;
  justify-content: center;
}

/* 深色主题 */
.dark-theme {
  background: #1a1a1a;
}

.dark-theme .sidebar {
  background: #252525;
  border-right-color: #333;
}

.dark-theme .main-content {
  background: #1a1a1a;
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    transform: translateX(-100%);
  }
  
  .sidebar:not(.collapsed) {
    transform: translateX(0);
  }
  
  .videos-grid {
    grid-template-columns: 1fr;
  }
}
</style>
