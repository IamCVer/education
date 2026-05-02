import request from '@/utils/request'

export default {
  // 上传视频
  uploadVideo(formData, onProgress) {
    return request.post('/api/v1/videos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        )
        if (onProgress) {
          onProgress(percentCompleted)
        }
      }
    })
  },
  
  // 获取我的视频（教师）
  getMyVideos(params) {
    return request.get('/api/v1/videos/my', { params })
  },
  
  // 获取所有可观看视频（学生）
  getAvailableVideos(params) {
    return request.get('/api/v1/videos', { params })
  },
  
  // 获取视频详情
  getVideo(id) {
    return request.get(`/api/v1/videos/${id}`)
  },
  
  // 更新视频
  updateVideo(id, data) {
    return request.put(`/api/v1/videos/${id}`, data)
  },
  
  // 删除视频
  deleteVideo(id) {
    return request.delete(`/api/v1/videos/${id}`)
  },
  
  // 更新观看进度
  updateProgress(videoId, progressSeconds) {
    return request.post(`/api/v1/videos/${videoId}/progress`, {
      progress_seconds: progressSeconds
    })
  },
  
  // 获取我的观看进度
  getMyProgress(videoId) {
    return request.get(`/api/v1/videos/${videoId}/progress`)
  },
  
  // 获取视频统计
  getVideoStats(videoId) {
    return request.get(`/api/v1/videos/${videoId}/stats`)
  }
}
