// axios 请求封装
import axios from 'axios'
import { Message } from 'element-ui'
import { normalizeRequestConfig } from './requestHelpers'

// 创建 axios 实例
const service = axios.create({
  // 使用相对路径，让Nginx代理处理
  // 浏览器会通过 /api/ 路径访问，Nginx会转发到 http://backend:8000
  baseURL: process.env.VUE_APP_BASE_API || '/',
  timeout: 300000, // 5分钟超时（视频上传需要较长时间）
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    const normalizedConfig = normalizeRequestConfig(config)
    // 从localStorage获取token
    const token = localStorage.getItem('userToken')
    if (token) {
      // 将token添加到请求头
      normalizedConfig.headers['Authorization'] = `Bearer ${token}`
    }
    return normalizedConfig
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    // 如果是 Blob 类型响应（如文件下载、音频流），直接返回完整的 response
    if (response.config.responseType === 'blob') {
      return response
    }
    // 否则返回 response.data（JSON 数据）
    const res = response.data
    return res
  },
  error => {
    console.error('响应错误:', error)

    // 处理各种错误情况
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // 未授权，清除token并跳转到登录页
          localStorage.removeItem('userToken')
          localStorage.removeItem('userInfo')
          Message.error('登录已过期，请重新登录')
          // 延迟跳转，避免重复跳转
          setTimeout(() => {
            if (window.location.pathname !== '/login') {
              window.location.href = '/login'
            }
          }, 1000)
          break
        case 403:
          Message.error('没有权限访问')
          break
        case 404:
          Message.error('请求的资源不存在')
          break
        case 500:
          Message.error('服务器错误')
          break
        default:
          Message.error(error.response.data?.detail || '请求失败')
      }
    } else if (error.request) {
      Message.error('网络错误，请检查网络连接')
    } else {
      Message.error('请求配置错误')
    }

    return Promise.reject(error)
  }
)

export default service

