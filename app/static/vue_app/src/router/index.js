// Vue Router 配置 (Vue 2)
import Vue from 'vue'
import VueRouter from 'vue-router'
import { useUserStore } from '@/stores/user'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/ChatPage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/group-chat',
    name: 'GroupChat',
    component: () => import('@/views/GroupChatPage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/mind-helper',
    name: 'MindHelper',
    beforeEnter: () => {
      // 外链跳转到心灵助手（通过 nginx 代理路径 /mindhelper）
      const token = localStorage.getItem('userToken')
      const baseUrl = process.env.VUE_APP_MIND_ASSIST_URL || '/mindhelper'
      const url = token ? `${baseUrl}?token=${token}` : baseUrl
      window.open(url, '_blank')
      return false
    }
  },
  {
    path: '/graph',
    name: 'Graph',
    beforeEnter: () => {
      // 外链跳转到知识图谱可视化
      window.open(process.env.VUE_APP_GRAPH_URL || 'http://localhost:7474/browser/', '_blank')
      return false
    }
  },
  // 视频功能路由
  {
    path: '/teacher/videos',
    name: 'TeacherVideos',
    component: () => import('@/views/TeacherVideos.vue'),
    meta: {
      requiresAuth: true,
      requiresRole: 'TEACHER'
    }
  },
  {
    path: '/student/videos',
    name: 'StudentVideos',
    component: () => import('@/views/StudentVideos.vue'),
    meta: {
      requiresAuth: true,
      requiresRole: 'STUDENT'
    }
  },
  {
    path: '/videos/player/:id',
    name: 'VideoPlayer',
    component: () => import('@/views/VideoPlayer.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/teacher/generate',
    name: 'ContentGenerator',
    component: () => import('@/views/ContentGenerator.vue'),
    meta: { requiresAuth: true, requiresRole: 'TEACHER' }
  },
  {
    path: '/teacher/agent',
    name: 'TeacherAgent',
    component: () => import('@/views/TeacherAgentEntry.vue'),
    meta: { requiresAuth: true, requiresRole: 'TEACHER' }
  },
  {
    path: '/student/generate',
    name: 'StudentContentGenerator',
    component: () => import('@/views/ContentGenerator.vue'),
    meta: { requiresAuth: true, requiresRole: 'STUDENT' }
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL || '/',
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 检查是否需要登录验证
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('userToken')

    if (!token) {
      // 未登录，跳转到登录页
      next('/login')
    } else {
      // 已登录，检查 token 是否过期
      try {
        const payload = JSON.parse(atob(token.split('.')[1]))
        const currentTime = Math.floor(Date.now() / 1000)

        if (payload.exp < currentTime) {
          // token 已过期，清除并跳转到登录页
          localStorage.removeItem('userToken')
          localStorage.removeItem('userInfo')
          next('/login')
        } else {
          // token 有效，检查角色权限
          if (to.meta.requiresRole) {
            const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
            const userRole = userInfo.role ? userInfo.role.toUpperCase() : ''
            const requiredRole = to.meta.requiresRole.toUpperCase()

            if (userRole !== requiredRole) {
              // 角色不匹配，阻止访问并重定向到聊天页面
              console.warn(`用户角色 ${userInfo.role} 无权访问 ${to.path}，需要角色 ${to.meta.requiresRole}`)
              next('/chat')
              return
            }
          }
          next()
        }
      } catch (error) {
        // token 解析失败，清除并跳转到登录页
        localStorage.removeItem('userToken')
        localStorage.removeItem('userInfo')
        next('/login')
      }
    }
  } else {
    // 不需要登录验证的页面
    const token = localStorage.getItem('userToken')
    if (token && (to.path === '/login' || to.path === '/register')) {
      // 已登录用户访问登录/注册页，直接跳转到聊天页
      next('/chat')
    } else {
      next()
    }
  }
})

export default router

