<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-card">
        <!-- 左侧信息面板 -->
        <div class="info-panel">
          <div class="info-content">
            <div class="logo">
              <h1>欢迎注册</h1>
            </div>
            <p class="subtitle">加入智能学业知识问答系统</p>
            <ul class="features-list">
              <li>
                <i class="el-icon-check"></i>
                <span>基于知识图谱的智能问答</span>
              </li>
              <li>
                <i class="el-icon-check"></i>
                <span>实时AI对话体验</span>
              </li>
              <li>
                <i class="el-icon-check"></i>
                <span>个性化学习助手</span>
              </li>
              <li>
                <i class="el-icon-check"></i>
                <span>安全可靠的数据保护</span>
              </li>
            </ul>
          </div>
        </div>

        <!-- 右侧注册表单 -->
        <div class="form-panel">
          <div class="form-content">
            <h2 class="form-title">创建账号</h2>
            
            <el-form
              ref="registerForm"
              :model="registerForm"
              :rules="registerRules"
              class="register-form"
              @submit.native.prevent="handleRegister"
            >
              <el-form-item prop="email">
                <el-input
                  v-model="registerForm.email"
                  placeholder="请输入邮箱地址"
                  prefix-icon="el-icon-message"
                  size="large"
                  autocomplete="email"
                >
                </el-input>
              </el-form-item>

              <el-form-item prop="password">
                <el-input
                  v-model="registerForm.password"
                  type="password"
                  placeholder="请输入密码（至少8位）"
                  prefix-icon="el-icon-lock"
                  size="large"
                  autocomplete="new-password"
                  show-password
                >
                </el-input>
                <!-- 密码强度指示器 -->
                <div v-if="registerForm.password" class="password-strength">
                  <div class="strength-bar">
                    <div 
                      class="strength-fill" 
                      :class="passwordStrength.class"
                      :style="{ width: passwordStrength.width }"
                    ></div>
                  </div>
                  <span class="strength-text" :class="passwordStrength.class">
                    {{ passwordStrength.text }}
                  </span>
                </div>
              </el-form-item>

              <el-form-item prop="confirmPassword">
                <el-input
                  v-model="registerForm.confirmPassword"
                  type="password"
                  placeholder="请确认密码"
                  prefix-icon="el-icon-lock"
                  size="large"
                  autocomplete="new-password"
                  show-password
                >
                </el-input>
              </el-form-item>

              <el-form-item prop="role">
                <el-select
                  v-model="registerForm.role"
                  placeholder="请选择角色"
                  size="large"
                  style="width: 100%"
                >
                  <el-option label="学生" value="student"></el-option>
                  <el-option label="教师" value="teacher"></el-option>
                  <el-option label="管理员" value="admin"></el-option>
                </el-select>
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  class="register-button"
                  :loading="loading"
                  @click="handleRegister"
                >
                  {{ loading ? '注册中...' : '注册' }}
                </el-button>
              </el-form-item>
            </el-form>

            <div class="form-footer">
              <span>已有账号？</span>
              <router-link to="/login" class="link">立即登录</router-link>
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
  name: 'RegisterView',
  
  data() {
    // 自定义验证器：确认密码
    const validateConfirmPassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请再次输入密码'))
      } else if (value !== this.registerForm.password) {
        callback(new Error('两次输入密码不一致'))
      } else {
        callback()
      }
    }

    return {
      registerForm: {
        email: '',
        password: '',
        confirmPassword: '',
        role: 'student'
      },
      registerRules: {
        email: [
          { required: true, message: '请输入邮箱地址', trigger: 'blur' },
          { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 8, message: '密码长度至少8位', trigger: 'blur' },
          { 
            pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/, 
            message: '密码必须包含大小写字母和数字', 
            trigger: 'blur' 
          }
        ],
        confirmPassword: [
          { required: true, message: '请确认密码', trigger: 'blur' },
          { validator: validateConfirmPassword, trigger: 'blur' }
        ],
        role: [
          { required: true, message: '请选择角色', trigger: 'change' }
        ]
      },
      loading: false
    }
  },

  computed: {
    ...mapStores(useUserStore),
    
    /**
    /**
     * 计算密码强度
     */
    passwordStrength() {
      const password = this.registerForm.password
      if (!password) {
        return { width: '0%', class: '', text: '' }
      }

      let strength = 0
      
      // 长度检查
      if (password.length >= 8) strength += 25
      if (password.length >= 12) strength += 10
      
      // 包含小写字母
      if (/[a-z]/.test(password)) strength += 20
      
      // 包含大写字母
      if (/[A-Z]/.test(password)) strength += 20
      
      // 包含数字
      if (/\d/.test(password)) strength += 15
      
      // 包含特殊字符
      if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength += 10

      if (strength < 40) {
        return { width: '33%', class: 'weak', text: '弱' }
      } else if (strength < 70) {
        return { width: '66%', class: 'medium', text: '中等' }
      } else {
        return { width: '100%', class: 'strong', text: '强' }
      }
    }
  },

  methods: {
    /**
     * 处理注册
     */
    async handleRegister() {
      try {
        // 验证表单
        await this.$refs.registerForm.validate()
        
        this.loading = true
        
        // 调用注册
        const success = await this.userStore.register({
          email: this.registerForm.email,
          password: this.registerForm.password,
          role: this.registerForm.role
        })
        
        if (success) {
          // 注册成功，延迟跳转到登录页
          setTimeout(() => {
            this.$router.push('/login')
          }, 2000)
        }
      } catch (error) {
        console.error('注册验证失败:', error)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.register-page {
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
.register-page::before {
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
.register-page::after {
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

.register-container {
  width: 100%;
  max-width: 1000px;
  position: relative;
  z-index: 10;
}

.register-card {
  display: flex;
  background: white;
  border-radius: 12px;
  box-shadow: 0 15px 50px rgba(125, 110, 204, 0.15);
  overflow: hidden;
  min-height: 600px;
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
  text-align: left;
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

.features-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.features-list li {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  font-size: 16px;
}

.features-list li i {
  font-size: 20px;
  margin-right: 15px;
  background: rgba(255, 255, 255, 0.2);
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
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

.register-form {
  margin-top: 30px;
}

.register-button {
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

/* 密码强度指示器 */
.password-strength {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.strength-bar {
  flex: 1;
  height: 4px;
  background: #e0e0e0;
  border-radius: 2px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  transition: all 0.3s;
  border-radius: 2px;
}

.strength-fill.weak {
  background: #f56c6c;
}

.strength-fill.medium {
  background: #e6a23c;
}

.strength-fill.strong {
  background: #67c23a;
}

.strength-text {
  font-size: 12px;
  font-weight: 600;
  min-width: 40px;
}

.strength-text.weak {
  color: #f56c6c;
}

.strength-text.medium {
  color: #e6a23c;
}

.strength-text.strong {
  color: #67c23a;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .register-card {
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

