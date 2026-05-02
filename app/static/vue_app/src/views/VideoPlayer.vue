<template>
  <div class="video-player-container">
    <!-- 顶部导航 -->
    <div class="top-nav">
      <el-button icon="el-icon-back" @click="goBack">返回</el-button>
      <h2 class="video-title">{{ video ? video.title : '加载中...' }}</h2>
      <div class="spacer"></div>
    </div>
    
    <!-- 视频播放器 -->
    <div class="player-wrapper">
      <!-- 加载遮罩层：使用 v-if 且放在播放器上方 -->
      <div v-if="loading" class="loading-overlay">
        <i class="el-icon-loading"></i>
        <p>加载视频中...</p>
      </div>
      
      <!-- 视频标签：不要使用 v-show 或 v-if，让 VideoJS 始终能找到它 -->
      <div class="video-container">
        <video 
          ref="videoPlayer" 
          class="video-js vjs-big-play-centered"
          playsinline
        ></video>
      </div>
    </div>
    
    <!-- 视频信息 -->
    <div v-if="video" class="video-info">
      <div class="info-section">
        <h3>📝 {{ video.title }}</h3>
        <div class="meta-info">
          <span><i class="el-icon-view"></i> {{ video.view_count || 0 }}次观看</span>
          <span v-if="!isTeacher && progress > 0">
            <i class="el-icon-pie-chart"></i> 您的进度: {{ progress }}%
          </span>
        </div>
        
        <div v-if="video.description" class="description">
          <h4>📄 视频描述</h4>
          <p>{{ video.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import videojs from 'video.js'
import 'video.js/dist/video-js.css'
import videosApi from '@/api/videos'

export default {
  name: 'VideoPlayer',
  data() {
    return {
      loading: true,
      video: null,
      player: null,
      lastSavedTime: 0,
      saveInterval: null,
      completedShown: false,
      progress: 0
    }
  },
  computed: {
    videoId() {
      return this.$route.params.id
    },
    isTeacher() {
      const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
      return userInfo.role && userInfo.role.toUpperCase() === 'TEACHER'
    }
  },
  mounted() {
    this.loadVideo()
  },
  beforeDestroy() {
    this.cleanup()
  },
  methods: {
    async loadVideo() {
      console.log('=== Step 1: loadVideo started ===')
      try {
        console.log(`=== Step 2: Fetching video info for ID: ${this.videoId} ===`)
        // 加载视频信息
        const videoData = await videosApi.getVideo(this.videoId)
        console.log('=== Step 3: Raw API Response ===', videoData)
        
        // 确保videoData不是null
        if (!videoData) {
          throw new Error('API returned empty data')
        }

        this.video = videoData
        
        // 调试：输出视频对象
        console.log('=== Step 4: Video Data Assigned ===')
        console.log('Full video object:', this.video)
        console.log('video_url:', this.video.video_url)
        console.log('oss_url:', this.video.oss_url)
        
        // 加载观看进度（仅学生）
        if (!this.isTeacher) {
          console.log('=== Step 5.1: Loading Progress (Student) ===')
          await this.loadProgress()
        } else {
          console.log('=== Step 5.2: Skipping Progress (Teacher) ===')
        }
        
        // 初始化播放器
        this.$nextTick(() => {
          this.initPlayer()
        })
      } catch (error) {
        console.error('=== ERROR in loadVideo ===', error)
        this.$message.error('加载视频失败: ' + (error.message || '未知错误'))
        // 暂时注释掉goBack以便查看错误日志
        // this.goBack()
      }
    },
    
    async loadProgress() {
      try {
        const progressData = await videosApi.getMyProgress(this.videoId)
        if (progressData && this.video.duration) {
          const progressSeconds = progressData.progress_seconds
          this.progress = Math.round((progressSeconds / this.video.duration) * 100)
          this.lastSavedTime = progressSeconds
        }
      } catch (error) {
        console.error('加载进度失败:', error)
      }
    },
    
    initPlayer() {
      console.log('=== initPlayer START ===')
      console.log('this.video:', this.video)
      console.log('this.video.video_url:', this.video ? this.video.video_url : 'NO VIDEO')
      console.log('this.$refs.videoPlayer:', this.$refs.videoPlayer)
      
      if (!this.video || !this.video.video_url) {
        this.$message.error('视频URL无效')
        return
      }
      
      // 清理旧的player实例（如果存在）
      if (this.player) {
        console.log('=== Disposing old player instance ===')
        this.player.dispose()
        this.player = null
      }
      
      const options = {
        controls: true,
        autoplay: false,
        preload: 'auto',
        fluid: true,
        aspectRatio: '16:9',
        playbackRates: [0.5, 0.75, 1, 1.25, 1.5, 2],
        sources: [{
          src: this.video.video_url,
          type: 'video/mp4'
        }]
      }
      
      console.log('=== VideoJS Options ===')
      console.log('Full options:', options)
      console.log('Source URL:', options.sources[0].src)
      
      try {
        this.player = videojs(this.$refs.videoPlayer, options)
        console.log('=== VideoJS Player Created ===', this.player)
        
        // 设置初始播放位置（学生端）
        if (!this.isTeacher && this.lastSavedTime > 0) {
          this.player.currentTime(this.lastSavedTime)
        }
        
        // 监听ready事件
        this.player.ready(() => {
          console.log('=== VideoJS Player Ready ===')
        })
        
        // 监听播放事件
        this.player.on('loadeddata', () => {
          console.log('=== Video loadeddata event ===')
          this.loading = false
        })
        
        this.player.on('error', (e) => {
          console.error('=== Video.js ERROR ===')
          console.error('Event:', e)
          console.error('Player error:', this.player.error())
          console.error('Error code:', this.player.error()?.code)
          console.error('Error message:', this.player.error()?.message)
          
          const errorCode = this.player.error()?.code
          const errorMessages = {
            1: 'MEDIA_ERR_ABORTED - 视频加载被中止',
            2: 'MEDIA_ERR_NETWORK - 网络错误',
            3: 'MEDIA_ERR_DECODE - 视频解码错误（格式不支持）',
            4: 'MEDIA_ERR_SRC_NOT_SUPPORTED - 视频源不支持'
          }
          
          const errorMsg = errorMessages[errorCode] || '未知错误'
          console.error('Error description:', errorMsg)
          
          this.$message.error(`视频加载失败: ${errorMsg}`)
          this.loading = false
        })
      } catch (error) {
        console.error('=== Error creating VideoJS player ===', error)
        this.$message.error('初始化播放器失败: ' + error.message)
        this.loading = false
      }
      
      
      // 学生端：自动保存进度
      if (!this.isTeacher) {
        this.player.on('timeupdate', () => {
          const currentTime = Math.floor(this.player.currentTime())
          
          // 每10秒保存一次进度
          if (currentTime - this.lastSavedTime >= 10) {
            this.saveProgress(currentTime)
          }
        })
        
        // 视频结束时保存
        this.player.on('ended', () => {
          const duration = Math.floor(this.player.duration())
          this.saveProgress(duration)
        })
      }
    },
    
    async saveProgress(currentTime) {
      try {
        const response = await videosApi.updateProgress(this.videoId, currentTime)
        this.lastSavedTime = currentTime
        
        // 更新进度百分比
        if (this.video.duration) {
          this.progress = Math.round((currentTime / this.video.duration) * 100)
          
          // 如果进度达到95%以上，且之前未完成，提示完成
          if (this.progress >= 95 && !this.completedShown) {
            this.$message.success('🎉 恭喜！您已完成本视频的学习')
            this.completedShown = true
          }
        }
      } catch (error) {
        console.error('保存进度失败:', error)
      }
    },
    
    cleanup() {
      // 保存最后的进度
      if (this.player && !this.isTeacher) {
        const currentTime = Math.floor(this.player.currentTime())
        if (currentTime > this.lastSavedTime) {
          this.saveProgress(currentTime)
        }
      }
      
      // 销毁播放器
      if (this.player) {
        this.player.dispose()
        this.player = null
      }
      
      // 清除定时器
      if (this.saveInterval) {
        clearInterval(this.saveInterval)
      }
    },
    
    goBack() {
      if (this.isTeacher) {
        this.$router.push('/teacher/videos')
      } else {
        this.$router.push('/student/videos')
      }
    }
  }
}
</script>

<style scoped>
.video-player-container {
  min-height: 100vh;
  background: #000;
  color: white;
}

.top-nav {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  background: #fff;
  padding: 10px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

.video-title {
  margin: 0 0 0 20px;
  font-size: 18px;
  color: #303133;
}

.player-wrapper {
  position: relative;
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}

.video-container {
  width: 100%;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #fff;
  z-index: 10;
}

.loading-overlay i {
  font-size: 40px;
  margin-bottom: 15px;
}

.video-info {
  max-width: 1000px;
  margin: 20px auto;
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}
/* 确保 videojs 充满容器 */
.video-js {
  width: 100%;
}
</style>

.info-section h3 {
  font-size: 24px;
  margin: 0 0 16px 0;
}

.meta-info {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  font-size: 14px;
  color: #aaa;
}

.meta-info span {
  display: flex;
  align-items: center;
  gap: 6px;
}

.description {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #333;
}

.description h4 {
  font-size: 16px;
  margin: 0 0 12px 0;
  color: #ddd;
}

.description p {
  font-size: 14px;
  line-height: 1.6;
  color: #aaa;
  white-space: pre-wrap;
}

/* 响应式 */
@media (max-width: 768px) {
  .top-nav {
    padding: 12px 16px;
  }
  
  .video-title {
    font-size: 16px;
  }
  
  .video-info {
    padding: 16px;
  }
}
</style>
