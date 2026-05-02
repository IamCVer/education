<template>
  <div class="video-card" :class="{ 'teacher-view': isTeacher, 'student-view': !isTeacher }">
    <div class="thumbnail" @click="handleClick">
      <img 
        :src="video.thumbnail_url || defaultThumbnail" 
        :alt="video.title" 
        @error="handleImageError"
      />
      <div class="duration">{{ formatDuration(video.duration) }}</div>
      
      <!-- 学生视图：显示进度条 -->
      <div v-if="!isTeacher && (progress > 0 || completed)" class="progress-overlay">
        <div class="progress-bar" :style="{ width: completed ? '100%' : progress + '%' }" :class="{ 'bar-completed': completed }"></div>
      </div>
      
      <!-- 播放图标 -->
      <div class="play-icon">
        <i class="el-icon-video-play"></i>
      </div>
    </div>
    
    <div class="info">
      <h3 class="title">{{ video.title }}</h3>
      <p v-if="video.description" class="description">{{ video.description }}</p>
      
      <div class="meta">
        <!-- 教师视图 -->
        <template v-if="isTeacher">
          <span class="status" :class="statusClass">
            {{ statusText }}
          </span>
          <span class="views">
            <i class="el-icon-view"></i> {{ video.view_count || 0 }}次
          </span>
        </template>
        
        <!-- 学生视图 -->
        <template v-else>
          <span v-if="completed" class="completed">
            <i class="el-icon-check"></i> 已完成
          </span>
          <span v-else-if="progress > 0" class="in-progress">
            <i class="el-icon-video-play"></i> 学习中 {{ progress }}%
          </span>
          <span v-else class="not-started">
            <i class="el-icon-circle-plus-outline"></i> 未开始
          </span>
        </template>
      </div>
      
      <!-- 操作按钮 -->
      <div class="actions">
        <template v-if="isTeacher">
          <el-button size="small" @click.stop="$emit('edit', video)">编辑</el-button>
          <el-button size="small" type="danger" @click.stop="$emit('delete', video)">删除</el-button>
          <el-button size="small" type="info" @click.stop="$emit('stats', video)">统计</el-button>
        </template>
        <template v-else>
          <el-button type="primary" size="small" @click.stop="handleClick">
            {{ completed ? '再次观看' : progress > 0 ? '继续观看' : '开始学习' }}
          </el-button>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VideoCard',
  props: {
    video: {
      type: Object,
      required: true
    },
    isTeacher: {
      type: Boolean,
      default: false
    },
    progress: {
      type: Number,
      default: 0
    },
    completed: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      defaultThumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgZmlsbD0iI2Y1ZjVmNSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7op4bpopHnvKnnlaXlm748L3RleHQ+PC9zdmc+'
    }
  },
  computed: {
    statusClass() {
      const statusMap = {
        'ready': 'status-ready',
        'processing': 'status-processing',
        'uploading': 'status-uploading',
        'failed': 'status-failed'
      }
      return statusMap[this.video.status] || ''
    },
    statusText() {
      const textMap = {
        'ready': '✓ 就绪',
        'processing': '⏳ 处理中',
        'uploading': '📤 上传中',
        'failed': '❌ 失败'
      }
      return textMap[this.video.status] || this.video.status
    }
  },
  methods: {
    formatDuration(seconds) {
      if (!seconds) return '00:00'
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    },
    handleClick() {
      this.$emit('play', this.video)
    },
    handleImageError(e) {
      e.target.src = this.defaultThumbnail
    }
  }
}
</script>

<style scoped>
.video-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
}

.video-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(108, 92, 231, 0.2);
}

.thumbnail {
  position: relative;
  width: 100%;
  height: 180px;
  overflow: hidden;
  background: #f5f5f5;
}

.thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.duration {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.progress-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: rgba(0, 0, 0, 0.3);
}

.progress-bar {
  height: 100%;
  background: #6c5ce7;
  transition: width 0.3s ease;
}

.progress-bar.bar-completed {
  background: #00b894;
}

.play-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60px;
  height: 60px;
  background: rgba(108, 92, 231, 0.9);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.thumbnail:hover .play-icon {
  opacity: 1;
}

.play-icon i {
  font-size: 28px;
  color: white;
  margin-left: 4px;
}

.info {
  padding: 16px;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.description {
  font-size: 14px;
  color: #666;
  margin: 0 0 12px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.meta {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 13px;
}

.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.status-ready {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-processing {
  background: #fff3e0;
  color: #e65100;
}

.status-uploading {
  background: #e3f2fd;
  color: #1565c0;
}

.status-failed {
  background: #ffebee;
  color: #c62828;
}

.views, .completed, .in-progress, .not-started {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #666;
}

.completed {
  color: #2e7d32;
  font-weight: 500;
}

.in-progress {
  color: #6c5ce7;
  font-weight: 500;
}

.actions {
  display: flex;
  gap: 8px;
}

.actions .el-button {
  flex: 1;
}

/* 深色主题 */
.dark-theme .video-card {
  background: #2a2a2a;
}

.dark-theme .title {
  color: #f5f5f5;
}

.dark-theme .description {
  color: #aaa;
}
</style>
