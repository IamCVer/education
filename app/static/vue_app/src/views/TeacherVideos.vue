<template>
  <div class="teacher-videos-container" :class="{ 'dark-theme': isDarkTheme }">
    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ collapsed: isSidebarCollapsed }">
      <div class="sidebar-header">
        <h1 class="app-title">📹 我的视频</h1>
        <div class="toggle-sidebar" @click="toggleSidebar">
          <i :class="isSidebarCollapsed ? 'el-icon-arrow-right' : 'el-icon-arrow-left'"></i>
        </div>
      </div>
      
      <!-- 上传按钮 -->
      <div class="new-video-btn" @click="showUploadDialog = true">
        <i class="el-icon-plus"></i>
        <span>上传新视频</span>
      </div>
      
      <!-- 筛选选项 -->
      <div class="filter-section">
        <h3 class="filter-title">筛选</h3>
        <div class="filter-item" 
             :class="{ active: currentFilter === 'all' }"
             @click="currentFilter = 'all'">
          <i class="el-icon-folder"></i>
          <span>全部视频</span>
          <span class="count">{{ totalCount }}</span>
        </div>
        <div class="filter-item"
             :class="{ active: currentFilter === 'ready' }"
             @click="currentFilter = 'ready'">
          <i class="el-icon-check"></i>
          <span>就绪</span>
        </div>
        <div class="filter-item"
             :class="{ active: currentFilter === 'processing' }"
             @click="currentFilter = 'processing'">
          <i class="el-icon-loading"></i>
          <span>处理中</span>
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
        <div class="view-options">
          <el-button 
            :type="viewMode === 'grid' ? 'primary' : ''" 
            icon="el-icon-menu"
            size="small"
            @click="viewMode = 'grid'"
          ></el-button>
          <el-button 
            :type="viewMode === 'list' ? 'primary' : ''" 
            icon="el-icon-s-operation"
            size="small"
            @click="viewMode = 'list'"
          ></el-button>
        </div>
      </div>
      
      <!-- 视频列表 -->
      <div v-if="loading" class="loading-container">
        <el-spinner></el-spinner>
        <p>加载中...</p>
      </div>
      
      <div v-else-if="filteredVideos.length === 0" class="empty-state">
        <i class="el-icon-video-camera"></i>
        <p>还没有上传视频</p>
        <el-button type="primary" @click="showUploadDialog = true">
          上传第一个视频
        </el-button>
      </div>
      
      <div v-else class="videos-grid" :class="viewMode">
        <video-card
          v-for="video in filteredVideos"
          :key="video.id"
          :video="video"
          :is-teacher="true"
          @edit="editVideo"
          @delete="confirmDelete"
          @stats="viewStats"
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
    
    <!-- 上传对话框 -->
    <el-dialog
      title="上传视频"
      :visible.sync="showUploadDialog"
      width="600px"
      :close-on-click-modal="false"
    >
      <video-uploader
        @upload-success="handleUploadSuccess"
        @cancel="showUploadDialog = false"
      />
    </el-dialog>
    
    <!-- 编辑对话框 -->
    <el-dialog
      title="编辑视频"
      :visible.sync="showEditDialog"
      width="500px"
    >
      <el-form v-if="editingVideo" :model="editingVideo" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="editingVideo.title"></el-input>
        </el-form-item>
        <el-form-item label="描述">
          <el-input type="textarea" v-model="editingVideo.description" :rows="4"></el-input>
        </el-form-item>
        <el-form-item label="可见性">
          <el-radio-group v-model="editingVideo.visibility">
            <el-radio label="public">公开</el-radio>
            <el-radio label="course_only">仅课程</el-radio>
            <el-radio label="private">私有</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </div>
    </el-dialog>

    <!-- 统计对话框 -->
    <el-dialog
      title="视频观看统计"
      :visible.sync="showStatsDialog"
      width="800px"
    >
      <div v-if="statsLoading" class="stats-loading">
        <i class="el-icon-loading"></i> 加载统计数据中...
      </div>
      <div v-else-if="currentStats" class="stats-content">
        <div class="stats-summary">
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="stat-box">
                <div class="stat-value">{{ currentStats.total_view_count }}</div>
                <div class="stat-label">总观看次数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-box">
                <div class="stat-value">{{ currentStats.unique_viewers }}</div>
                <div class="stat-label">独立观看人数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-box">
                <div class="stat-value">{{ currentStats.avg_progress_percent }}%</div>
                <div class="stat-label">平均进度</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-box">
                <div class="stat-value">{{ currentStats.completion_rate }}%</div>
                <div class="stat-label">完成率</div>
              </div>
            </el-col>
          </el-row>
        </div>

        <el-table :data="currentStats.viewers" style="width: 100%" max-height="400">
          <el-table-column prop="username" label="用户"></el-table-column>
          <el-table-column label="观看进度">
            <template slot-scope="scope">
              <el-progress :percentage="scope.row.progress_percent"></el-progress>
            </template>
          </el-table-column>
          <el-table-column label="完成状态">
            <template slot-scope="scope">
              <el-tag :type="scope.row.completed ? 'success' : 'info'">
                {{ scope.row.completed ? '已完成' : '观看中' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="最后观看时间">
            <template slot-scope="scope">
              {{ formatDate(scope.row.last_watched_at) }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import VideoCard from '@/components/VideoCard.vue'
import VideoUploader from '@/components/VideoUploader.vue'
import videosApi from '@/api/videos'

export default {
  name: 'TeacherVideos',
  components: {
    VideoCard,
    VideoUploader
  },
  data() {
    return {
      isDarkTheme: false,
      isSidebarCollapsed: false,
      showUploadDialog: false,
      showEditDialog: false,
      loading: false,
      searchQuery: '',
      currentFilter: 'all',
      viewMode: 'grid', // 'grid' or 'list'
      videos: [],
      editingVideo: null,
      currentPage: 1,
      pageSize: 12,
      totalCount: 0,
      showStatsDialog: false,
      statsLoading: false,
      currentStats: null
    }
  },
  computed: {
    filteredVideos() {
      let filtered = this.videos
      
      // 按状态筛选
      if (this.currentFilter !== 'all') {
        filtered = filtered.filter(v => v.status === this.currentFilter)
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
    }
  },
  mounted() {
    this.loadVideos()
  },
  methods: {
    toggleSidebar() {
      this.isSidebarCollapsed = !this.isSidebarCollapsed
    },
    
    async loadVideos() {
      this.loading = true
      try {
        const response = await videosApi.getMyVideos({
          page: this.currentPage,
          page_size: this.pageSize
        })
        // axios拦截器已经返回了response.data，所以response就是数据本身
        this.videos = response.videos || []
        this.totalCount = response.total || this.videos.length
      } catch (error) {
        console.error('加载视频失败:', error)
        this.$message.error('加载视频列表失败')
      } finally {
        this.loading = false
      }
    },
    
    handleUploadSuccess(video) {
      this.showUploadDialog = false
      this.$message.success('视频上传成功！')
      this.loadVideos()
    },
    
    editVideo(video) {
      this.editingVideo = { ...video }
      this.showEditDialog = true
    },
    
    async saveEdit() {
      try {
        await videosApi.updateVideo(this.editingVideo.id, {
          title: this.editingVideo.title,
          description: this.editingVideo.description,
          visibility: this.editingVideo.visibility
        })
        this.$message.success('保存成功')
        this.showEditDialog = false
        this.loadVideos()
      } catch (error) {
        console.error('保存失败:', error)
        this.$message.error('保存失败')
      }
    },
    
    confirmDelete(video) {
      this.$confirm(`确定要删除视频"${video.title}"吗？`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          await videosApi.deleteVideo(video.id)
          this.$message.success('删除成功')
          this.loadVideos()
        } catch (error) {
          console.error('删除失败:', error)
          this.$message.error('删除失败')
        }
      }).catch(() => {})
    },
    
    async viewStats(video) {
      this.showStatsDialog = true
      this.statsLoading = true
      try {
        this.currentStats = await videosApi.getVideoStats(video.id)
      } catch (error) {
        console.error('获取统计数据失败:', error)
        this.$message.error('获取统计数据失败')
        this.showStatsDialog = false
      } finally {
        this.statsLoading = false
      }
    },

    formatDate(dateStr) {
      if (!dateStr) return '-'
      const date = new Date(dateStr)
      return date.toLocaleString()
    },
    
    playVideo(video) {
      this.$router.push(`/videos/player/${video.id}`)
    },
    
    handlePageChange(page) {
      this.currentPage = page
      this.loadVideos()
    }
  }
}
</script>

<style scoped>
.teacher-videos-container {
  display: flex;
  height: 100vh;
  background: #f8f7fd;
}

/* 侧边栏样式（复用ChatPage样式） */
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

.new-video-btn {
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
  transition: transform 0.2s;
}

.new-video-btn:hover {
  transform: translateY(-2px);
}

.sidebar.collapsed .new-video-btn span {
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

.filter-item .count {
  margin-left: auto;
  background: #e0e0e0;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
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
  gap: 16px;
}

.search-box {
  flex: 1;
  max-width: 400px;
}

.view-options {
  display: flex;
  gap: 8px;
}

.loading-container {
  text-align: center;
  padding: 60px 20px;
  color: #999;
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
  margin-bottom: 24px;
}

.videos-grid {
  display: grid;
  gap: 20px;
}

.videos-grid.grid {
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

.videos-grid.list {
  grid-template-columns: 1fr;
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
  
  .videos-grid.grid {
    grid-template-columns: 1fr;
  }
}

.stats-loading {
  padding: 40px;
  text-align: center;
  color: #909399;
}

.stats-summary {
  margin-bottom: 24px;
}

.stat-box {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #6c5ce7;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #909399;
}
</style>
