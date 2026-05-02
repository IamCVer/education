// 认证相关API
import request from '@/utils/request'

/**
 * 用户登录
 * @param {string} username - 用户名（邮箱）
 * @param {string} password - 密码
 */
export function login(username, password) {
  // 使用 URLSearchParams 格式化表单数据
  const formData = new URLSearchParams()
  formData.append('username', username)
  formData.append('password', password)
  
  return request({
    url: '/api/v1/auth/login',
    method: 'post',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    data: formData
  })
}

/**
 * 用户注册
 * @param {Object} userData - 用户注册数据
 * @param {string} userData.email - 邮箱
 * @param {string} userData.password - 密码
 * @param {string} userData.role - 角色（student/teacher/admin）
 */
export function register(userData) {
  return request({
    url: '/api/v1/auth/register',
    method: 'post',
    data: userData
  })
}

/**
 * 获取当前用户信息
 */
export function getCurrentUser() {
  return request({
    url: '/api/v1/auth/me',
    method: 'get'
  })
}

/**
 * 退出登录
 */
export function logout() {
  return request({
    url: '/api/v1/auth/logout',
    method: 'post'
  })
}

