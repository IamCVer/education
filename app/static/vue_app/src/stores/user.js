// 用户状态管理 Store (Pinia)
import { defineStore } from 'pinia'
import { login, register, getCurrentUser } from '@/api/auth'
import { Message } from 'element-ui'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('userToken') || '',
    userInfo: JSON.parse(localStorage.getItem('userInfo') || 'null'),
    rememberMe: localStorage.getItem('rememberMe') === 'true',
    savedCredentials: {
      username: localStorage.getItem('savedUsername') || '',
      password: localStorage.getItem('savedPassword') || ''
    }
  }),

  getters: {
    // 是否已登录
    isLoggedIn: (state) => !!state.token,
    
    // 获取用户ID
    userId: (state) => state.userInfo?.id || null,
    
    // 获取用户名
    username: (state) => state.userInfo?.email || '',
    
    // 获取用户角色
    userRole: (state) => state.userInfo?.role || 'student'
  },

  actions: {
    /**
     * 用户登录
     * @param {string} username - 用户名（邮箱）
     * @param {string} password - 密码
     * @param {boolean} rememberMe - 是否记住密码
     */
    async login(username, password, rememberMe = false) {
      try {
        // 调用登录API
        const response = await login(username, password)
        
        if (response && response.access_token) {
          // 保存token
          this.token = response.access_token
          localStorage.setItem('userToken', response.access_token)
          
          // 解析token获取用户信息
          const userInfo = this.parseJWT(response.access_token)
          userInfo.email = username // 保存邮箱
          
          this.userInfo = userInfo
          localStorage.setItem('userInfo', JSON.stringify(userInfo))
          
          // 处理记住密码
          this.rememberMe = rememberMe
          localStorage.setItem('rememberMe', String(rememberMe))
          
          if (rememberMe) {
            localStorage.setItem('savedUsername', username)
            localStorage.setItem('savedPassword', password)
          } else {
            localStorage.removeItem('savedUsername')
            localStorage.removeItem('savedPassword')
          }
          
          // 获取完整的用户信息（非关键操作，失败不影响登录）
          try {
            await this.fetchUserInfo()
          } catch (err) {
            console.warn('获取用户信息失败，但登录已成功:', err)
          }
          
          Message.success('登录成功')
          return true
        } else {
          Message.error('登录失败：未获取到token')
          return false
        }
      } catch (error) {
        console.error('登录失败:', error)
        const errorMsg = error.response?.data?.detail || '登录失败，请检查用户名和密码'
        Message.error(errorMsg)
        return false
      }
    },

    /**
     * 用户注册
     * @param {Object} userData - 用户注册数据
     */
    async register(userData) {
      try {
        const response = await register(userData)
        
        if (response && response.id) {
          Message.success('注册成功，请登录')
          return true
        } else {
          Message.error('注册失败')
          return false
        }
      } catch (error) {
        console.error('注册失败:', error)
        const errorMsg = error.response?.data?.detail || '注册失败，请稍后重试'
        Message.error(errorMsg)
        return false
      }
    },

    /**
     * 获取当前用户信息
     */
    async fetchUserInfo() {
      try {
        const userInfo = await getCurrentUser()
        this.userInfo = userInfo
        localStorage.setItem('userInfo', JSON.stringify(userInfo))
        return userInfo
      } catch (error) {
        console.error('获取用户信息失败:', error)
        return null
      }
    },

    /**
     * 退出登录
     */
    logout() {
      // 清除状态
      this.token = ''
      this.userInfo = null
      
      // 清除localStorage（保留记住密码的数据）
      localStorage.removeItem('userToken')
      localStorage.removeItem('userInfo')
      
      Message.success('已退出登录')
    },

    /**
     * 解析JWT token
     * @param {string} token - JWT token
     */
    parseJWT(token) {
      try {
        const base64Url = token.split('.')[1]
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
        const jsonPayload = decodeURIComponent(
          atob(base64)
            .split('')
            .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
            .join('')
        )
        
        const payload = JSON.parse(jsonPayload)
        return {
          id: parseInt(payload.sub) || null,
          exp: payload.exp,
          iat: payload.iat
        }
      } catch (error) {
        console.error('解析JWT失败:', error)
        return { id: null }
      }
    },

    /**
     * 检查token是否过期
     */
    isTokenExpired() {
      if (!this.token || !this.userInfo?.exp) {
        return true
      }
      
      const currentTime = Math.floor(Date.now() / 1000)
      return this.userInfo.exp < currentTime
    },

    /**
     * 加载保存的凭据
     */
    loadSavedCredentials() {
      if (this.rememberMe) {
        return {
          username: localStorage.getItem('savedUsername') || '',
          password: localStorage.getItem('savedPassword') || ''
        }
      }
      return null
    }
  }
})

