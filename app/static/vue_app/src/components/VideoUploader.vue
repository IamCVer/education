<template>
  <div class="video-uploader">
    <div 
      class="upload-area" 
      :class="{ dragging: isDragging, 'has-file': selectedFile }"
      @drop.prevent="handleDrop" 
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      @click="triggerFileInput"
    >
      <input 
        type="file" 
        ref="fileInput" 
        @change="handleFileSelect"
        accept="video/*" 
        style="display: none"
      />
      
      <div v-if="!selectedFile" class="upload-prompt">
        <i class="el-icon-upload"></i>
        <p class="main-text">拖拽视频文件到这里</p>
        <p class="hint">或点击选择文件</p>
        <p class="format">支持: MP4, AVI, MOV (最大500MB)</p>
      </div>
      
      <div v-else class="file-info">
        <i class="el-icon-video-camera"></i>
        <p class="filename">{{ selectedFile.name }}</p>
        <p class="filesize">{{ formatFileSize(selectedFile.size) }}</p>
      </div>
    </div>
    
    <!-- 上传进度 -->
    <div v-if="uploading" class="upload-progress">
      <el-progress 
        :percentage="uploadProgress" 
        :status="uploadProgress === 100 ? 'success' : ''"
      ></el-progress>
      <p class="progress-text">
        {{ uploadProgress === 100 ? '上传完成，正在处理...' : `上传中... ${uploadProgress}%` }}
      </p>
    </div>
    
    <!-- 视频信息表单 -->
    <div v-if="selectedFile && !uploading" class="video-info-form">
      <el-form :model="videoForm" label-width="80px">
        <el-form-item label="视频标题" required>
          <el-input 
            v-model="videoForm.title" 
            placeholder="请输入视频标题"
            maxlength="100"
            show-word-limit
          ></el-input>
        </el-form-item>
        
        <el-form-item label="视频描述">
          <el-input 
            type="textarea" 
            v-model="videoForm.description" 
            placeholder="请输入视频描述（选填）"
            :rows="4"
            maxlength="500"
            show-word-limit
          ></el-input>
        </el-form-item>
        
        <el-form-item label="所属课程">
          <div style="display: flex; gap: 10px; align-items: center;">
            <el-select 
              v-model="videoForm.course_id" 
              placeholder="请选择课程（可选）"
              clearable
              style="flex: 1;"
            >
              <el-option
                v-for="course in courses"
                :key="course.id"
                :label="course.name"
                :value="course.id"
              />
            </el-select>
            <el-button 
              type="text" 
              icon="el-icon-plus"
              @click="showCreateCourseDialog = true"
            >
              创建课程
            </el-button>
          </div>
          <p class="visibility-hint">
            选择课程后，视频将自动添加到该课程中
          </p>
        </el-form-item>
        
        <el-form-item label="可见性">
          <el-radio-group v-model="videoForm.visibility">
            <el-radio label="public">公开</el-radio>
            <el-radio label="course_only">仅课程</el-radio>
            <el-radio label="private">私有</el-radio>
          </el-radio-group>
          <p class="visibility-hint">
            {{ visibilityHint }}
          </p>
        </el-form-item>
      </el-form>
      
      <div class="actions">
        <el-button @click="cancelUpload">取消</el-button>
        <el-button 
          type="primary" 
          @click="uploadVideo"
          :disabled="!videoForm.title"
        >
          开始上传
        </el-button>
      </div>
    </div>
    
    <!-- 创建课程对话框 -->
    <el-dialog
      title="创建新课程"
      :visible.sync="showCreateCourseDialog"
      width="450px"
    >
      <el-form :model="newCourse" label-width="80px">
        <el-form-item label="课程名称" required>
          <el-input 
            v-model="newCourse.name" 
            placeholder="请输入课程名称"
            maxlength="100"
          />
        </el-form-item>
        <el-form-item label="课程描述">
          <el-input 
            type="textarea" 
            v-model="newCourse.description" 
            placeholder="请输入课程描述（选填）"
            :rows="3"
            maxlength="500"
          />
        </el-form-item>
        <el-form-item label="发布状态">
          <el-switch 
            v-model="newCourse.is_published"
            active-text="已发布"
            inactive-text="草稿"
          />
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="showCreateCourseDialog = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="createCourse"
          :disabled="!newCourse.name"
        >
          创建
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import videosApi from '@/api/videos'
import coursesApi from '@/api/courses'

export default {
  name: 'VideoUploader',
  data() {
    return {
      isDragging: false,
      selectedFile: null,
      uploading: false,
      uploadProgress: 0,
      videoForm: {
        title: '',
        description: '',
        visibility: 'course_only',
        course_id: null
      },
      courses: [],
      showCreateCourseDialog: false,
      newCourse: {
        name: '',
        description: '',
        is_published: true
      }
    }
  },
  mounted() {
    this.loadCourses()
  },
  computed: {
    visibilityHint() {
      const hints = {
        'public': '所有人都可以观看此视频',
        'course_only': '只有加入课程的学生可以观看',
        'private': '只有您自己可以看到此视频'
      }
      return hints[this.videoForm.visibility] || ''
    }
  },
  methods: {
    triggerFileInput() {
      if (!this.uploading) {
        this.$refs.fileInput.click()
      }
    },
    
    handleDrop(e) {
      this.isDragging = false
      const files = e.dataTransfer.files
      if (files.length > 0) {
        this.handleFile(files[0])
      }
    },
    
    handleFileSelect(e) {
      const files = e.target.files
      if (files.length > 0) {
        this.handleFile(files[0])
      }
    },
    
    handleFile(file) {
      // 验证文件类型
      if (!file.type.startsWith('video/')) {
        this.$message.error('请选择视频文件')
        return
      }
      
      // 验证文件大小 (500MB)
      const maxSize = 500 * 1024 * 1024
      if (file.size > maxSize) {
        this.$message.error('文件大小不能超过500MB')
        return
      }
      
      this.selectedFile = file
      // 自动填充标题（去掉扩展名）
      if (!this.videoForm.title) {
        this.videoForm.title = file.name.replace(/\.[^/.]+$/, '')
      }
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
    },
    
    async uploadVideo() {
      if (!this.selectedFile || !this.videoForm.title) {
        this.$message.warning('请填写视频标题')
        return
      }
      
      const formData = new FormData()
      formData.append('file', this.selectedFile)
      formData.append('title', this.videoForm.title)
      formData.append('description', this.videoForm.description)
      formData.append('visibility', this.videoForm.visibility)
      if (this.videoForm.course_id) {
        formData.append('course_id', this.videoForm.course_id)
      }
      
      this.uploading = true
      this.uploadProgress = 0
      
      try {
        const response = await videosApi.uploadVideo(formData, (progress) => {
          this.uploadProgress = progress
        })
        
        this.$message.success('视频上传成功！')
        this.$emit('upload-success', response.data)
        this.resetForm()
      } catch (error) {
        console.error('上传失败:', error)
        this.$message.error(error.response?.data?.detail || '视频上传失败')
      } finally {
        this.uploading = false
      }
    },
    
    cancelUpload() {
      this.resetForm()
      this.$emit('cancel')
    },
    
    async loadCourses() {
      try {
        const response = await coursesApi.getMyCourses()
        this.courses = response || []
      } catch (error) {
        console.error('加载课程失败:', error)
      }
    },
    
    async createCourse() {
      if (!this.newCourse.name) {
        this.$message.warning('请输入课程名称')
        return
      }
      
      try {
        const response = await coursesApi.createCourse(this.newCourse)
        this.$message.success('课程创建成功')
        this.showCreateCourseDialog = false
        await this.loadCourses()
        this.videoForm.course_id = response.id
        // 重置新课程表单
        this.newCourse = {
          name: '',
          description: '',
          is_published: true
        }
      } catch (error) {
        console.error('创建课程失败:', error)
        this.$message.error('创建课程失败')
      }
    },
    
    resetForm() {
      this.selectedFile = null
      this.uploadProgress = 0
      this.videoForm = {
        title: '',
        description: '',
        visibility: 'course_only',
        course_id: null
      }
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
    }
  }
}
</script>

<style scoped>
.video-uploader {
  width: 100%;
}

.upload-area {
  border: 2px dashed #ddd;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafafa;
}

.upload-area:hover {
  border-color: #6c5ce7;
  background: #f8f7fd;
}

.upload-area.dragging {
  border-color: #6c5ce7;
  background: #f0edff;
  transform: scale(1.02);
}

.upload-area.has-file {
  border-color: #6c5ce7;
  background: #f8f7fd;
}

.upload-prompt .el-icon-upload {
  font-size: 64px;
  color: #6c5ce7;
  margin-bottom: 16px;
}

.main-text {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.hint {
  font-size: 14px;
  color: #666;
  margin: 0 0 12px 0;
}

.format {
  font-size: 12px;
  color: #999;
  margin: 0;
}

.file-info {
  padding: 20px;
}

.file-info .el-icon-video-camera {
  font-size: 48px;
  color: #6c5ce7;
  margin-bottom: 12px;
}

.filename {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 4px 0;
  word-break: break-all;
}

.filesize {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.upload-progress {
  margin-top: 24px;
  padding: 20px;
  background: #f8f7fd;
  border-radius: 8px;
}

.progress-text {
  text-align: center;
  margin-top: 12px;
  font-size: 14px;
  color: #666;
}

.video-info-form {
  margin-top: 24px;
  padding: 24px;
  background: white;
  border-radius: 12px;
  border: 1px solid #eee;
}

.visibility-hint {
  font-size: 12px;
  color: #999;
  margin: 8px 0 0 0;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #eee;
}

/* 深色主题 */
.dark-theme .upload-area {
  background: #2a2a2a;
  border-color: #444;
}

.dark-theme .upload-area:hover {
  background: #333;
}

.dark-theme .video-info-form {
  background: #2a2a2a;
  border-color: #444;
}

.dark-theme .main-text,
.dark-theme .filename {
  color: #f5f5f5;
}
</style>
