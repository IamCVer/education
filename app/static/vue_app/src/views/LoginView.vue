<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-card">
        <!-- 左侧信息面板 -->
        <div class="info-panel">
          <div class="info-content">
            <div class="logo">
              <h1>欢迎登录</h1>
            </div>
            <p class="subtitle">RAG+知识图谱本科智慧教学系统</p>
            <div class="features">
              <div class="feature-item">
                <i class="el-icon-chat-dot-round"></i>
                <span>智能问答对话</span>
              </div>
              <div class="feature-item">
                <i class="el-icon-share"></i>
                <span>知识图谱可视化</span>
              </div>
              <div class="feature-item">
                <i class="el-icon-star-off"></i>
                <span>心灵助手服务</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧登录表单 -->
        <div class="form-panel">
          <div class="form-content">
            <h2 class="form-title">登录</h2>
            
            <el-form
              ref="loginForm"
              :model="loginForm"
              :rules="loginRules"
              class="login-form"
              @submit.native.prevent="handleLogin"
            >
              <el-form-item prop="username">
                <el-input
                  v-model="loginForm.username"
                  placeholder="请输入邮箱"
                  prefix-icon="el-icon-user"
                  size="large"
                  autocomplete="username"
                >
                </el-input>
              </el-form-item>

              <el-form-item prop="password">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="请输入密码"
                  prefix-icon="el-icon-lock"
                  size="large"
                  autocomplete="current-password"
                  show-password
                >
                </el-input>
              </el-form-item>

              <el-form-item>
                <div class="form-options">
                  <el-checkbox v-model="loginForm.rememberMe">
                    记住密码
                  </el-checkbox>
                  <el-checkbox v-model="loginForm.autoLogin">
                    自动登录
                  </el-checkbox>
                </div>
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  class="login-button"
                  :loading="loading"
                  @click="handleLogin"
                >
                  {{ loading ? '登录中...' : '登录' }}
                </el-button>
              </el-form-item>
            </el-form>

            <div class="form-footer">
              <span>没有账号？</span>
              <router-link to="/register" class="link">立即注册</router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapStores } from 'pinia'
import { useUserStore } from '@/stores/user'

export default {
  name: 'LoginView',
  
  data() {
    return {
      loginForm: {
        username: '',
        password: '',
        rememberMe: false,
        autoLogin: false
      },
      loginRules: {
        username: [
          { required: true, message: '请输入邮箱地址', trigger: 'blur' },
          { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码长度至少6位', trigger: 'blur' }
        ]
      },
      loading: false
    }
  },

  computed: {
    ...mapStores(useUserStore)
  },

  mounted() {
    // 加载保存的凭据
    this.loadSavedCredentials()
    
    // 如果勾选了自动登录，则自动登录
    if (this.loginForm.autoLogin && this.loginForm.username && this.loginForm.password) {
      this.handleLogin()
    }
  },

  methods: {
    /**
     * 处理登录
     */
    async handleLogin() {
      try {
        // 验证表单
        await this.$refs.loginForm.validate()
        
        this.loading = true
        
        // 调用登录
        const success = await this.userStore.login(
          this.loginForm.username,
          this.loginForm.password,
          this.loginForm.rememberMe
        )
        
        if (success) {
          // 保存自动登录选项
          localStorage.setItem('autoLogin', String(this.loginForm.autoLogin))
          
          // 登录成功，跳转到聊天页面
          this.$router.push('/chat')
        }
      } catch (error) {
        console.error('登录验证失败:', error)
      } finally {
        this.loading = false
      }
    },

    /**
     * 加载保存的凭据
     */
    loadSavedCredentials() {
      const savedCredentials = this.userStore.loadSavedCredentials()
      
      if (savedCredentials) {
        this.loginForm.username = savedCredentials.username
        this.loginForm.password = savedCredentials.password
        this.loginForm.rememberMe = true
      }
      
      // 加载自动登录选项
      const autoLogin = localStorage.getItem('autoLogin') === 'true'
      this.loginForm.autoLogin = autoLogin
    }
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e4dffd;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

/* 波浪形装饰 - 左下角 */
.login-page::before {
  content: '';
  position: absolute;
  bottom: -100px;
  left: -100px;
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, #8b7fd6 0%, #9f8ce5 100%);
  border-radius: 45% 55% 50% 50% / 60% 60% 40% 40%;
  opacity: 0.8;
  z-index: 1;
}

/* 波浪形装饰 - 右上角 */
.login-page::after {
  content: '';
  position: absolute;
  top: -150px;
  right: -150px;
  width: 700px;
  height: 700px;
  background: linear-gradient(135deg, #7d6ecc 0%, #8f7dd9 100%);
  border-radius: 50% 45% 55% 50% / 40% 50% 50% 60%;
  opacity: 0.7;
  z-index: 1;
}

.login-container {
  width: 100%;
  max-width: 1000px;
  position: relative;
  z-index: 10;
}

.login-card {
  display: flex;
  background: white;
  border-radius: 12px;
  box-shadow: 0 15px 50px rgba(125, 110, 204, 0.15);
  overflow: hidden;
  min-height: 500px;
}

/* 左侧信息面板 */
.info-panel {
  flex: 1;
  background: linear-gradient(135deg, #8b7fd6 0%, #9f8ce5 100%);
  color: white;
  padding: 60px 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.info-content {
  text-align: center;
}

.logo h1 {
  font-size: 32px;
  margin-bottom: 10px;
  font-weight: 600;
}

.subtitle {
  font-size: 16px;
  margin-bottom: 40px;
  opacity: 0.9;
}

.features {
  margin-top: 40px;
}

.feature-item {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  font-size: 16px;
}

.feature-item i {
  font-size: 24px;
  margin-right: 10px;
}

/* 右侧表单面板 */
.form-panel {
  flex: 1;
  padding: 60px 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-content {
  width: 100%;
  max-width: 400px;
}

.form-title {
  font-size: 28px;
  margin-bottom: 30px;
  color: #333;
  text-align: center;
}

.login-form {
  margin-top: 30px;
}

.form-options {
  display: flex;
  justify-content: space-between;
  width: 100%;
}

.login-button {
  width: 100%;
  height: 45px;
  font-size: 16px;
  font-weight: 600;
  margin-top: 10px;
}

.form-footer {
  text-align: center;
  margin-top: 20px;
  color: #666;
}

.link {
  color: #8b7fd6;
  text-decoration: none;
  margin-left: 5px;
  font-weight: 600;
}

.link:hover {
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-card {
    flex-direction: column;
  }

  .info-panel {
    padding: 40px 20px;
  }

  .form-panel {
    padding: 40px 20px;
  }

  .logo h1 {
    font-size: 24px;
  }

  .subtitle {
    font-size: 14px;
  }

  .form-title {
    font-size: 24px;
  }
}
</style>

