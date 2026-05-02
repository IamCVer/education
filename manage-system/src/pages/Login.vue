<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-card">
        <!-- 左侧信息面板 -->
        <div class="info-panel">
          <div class="info-content">
            <div class="logo">
              <h1>管理员登录</h1>
            </div>
            <p class="subtitle">后台管理系统</p>
            <div class="features">
              <div class="feature-item">
                <md-icon>people</md-icon>
                <span>用户管理</span>
              </div>
              <div class="feature-item">
                <md-icon>assessment</md-icon>
                <span>数据统计</span>
              </div>
              <div class="feature-item">
                <md-icon>settings</md-icon>
                <span>系统配置</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧登录表单 -->
        <div class="form-panel">
          <div class="form-content">
            <h2 class="form-title">登录</h2>
            
            <form class="login-form" @submit.prevent="handleLogin">
              <md-field :class="{ 'md-invalid': errors.username }">
                <label>用户名</label>
                <md-icon>person</md-icon>
                <md-input 
                  v-model="loginForm.username" 
                  type="text"
                  @input="clearError('username')"
                ></md-input>
                <span class="md-error" v-if="errors.username">{{ errors.username }}</span>
              </md-field>

              <md-field :class="{ 'md-invalid': errors.password }">
                <label>密码</label>
                <md-icon>lock</md-icon>
                <md-input 
                  v-model="loginForm.password" 
                  type="password"
                  @input="clearError('password')"
                ></md-input>
                <span class="md-error" v-if="errors.password">{{ errors.password }}</span>
              </md-field>

              <div class="form-options">
                <md-checkbox v-model="loginForm.rememberMe" class="md-primary">
                  记住密码
                </md-checkbox>
              </div>

              <md-button 
                type="submit"
                class="md-raised md-primary login-button"
                :disabled="loading"
              >
                <md-progress-spinner 
                  v-if="loading"
                  :md-diameter="20" 
                  :md-stroke="2" 
                  md-mode="indeterminate"
                  class="spinner"
                ></md-progress-spinner>
                <span v-else>登录</span>
              </md-button>

              <div v-if="errorMessage" class="error-message">
                <md-icon>error</md-icon>
                <span>{{ errorMessage }}</span>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Login',
  
  data() {
    return {
      loginForm: {
        username: '',
        password: '',
        rememberMe: false
      },
      errors: {
        username: '',
        password: ''
      },
      errorMessage: '',
      loading: false
    };
  },

  mounted() {
    // 加载保存的凭据
    this.loadSavedCredentials();
  },

  methods: {
    /**
     * 验证表单
     */
    validateForm() {
      let isValid = true;
      this.errors = {
        username: '',
        password: ''
      };

      if (!this.loginForm.username) {
        this.errors.username = '请输入用户名';
        isValid = false;
      }

      if (!this.loginForm.password) {
        this.errors.password = '请输入密码';
        isValid = false;
      } else if (this.loginForm.password.length < 6) {
        this.errors.password = '密码长度至少6位';
        isValid = false;
      }

      return isValid;
    },

    /**
     * 清除错误信息
     */
    clearError(field) {
      this.errors[field] = '';
      this.errorMessage = '';
    },

    /**
     * 处理登录
     */
    async handleLogin() {
      // 验证表单
      if (!this.validateForm()) {
        return;
      }

      this.loading = true;
      this.errorMessage = '';

      try {
        // 调用后端登录 API (使用 form-data 格式)
        const formData = new URLSearchParams();
        formData.append('username', this.loginForm.username);
        formData.append('password', this.loginForm.password);
        
        const response = await axios.post('/api/v1/auth/login', formData, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        });

        if (response.data && response.data.access_token) {
          // 保存 token
          localStorage.setItem('admin_token', response.data.access_token);
          
          // 保存用户信息
          if (response.data.user) {
            localStorage.setItem('admin_user', JSON.stringify(response.data.user));
          }

          // 如果勾选了记住密码，保存凭据
          if (this.loginForm.rememberMe) {
            this.saveCredentials();
          } else {
            this.clearSavedCredentials();
          }

          // 显示成功消息
          this.$notify({
            message: '登录成功！',
            icon: 'check_circle',
            horizontalAlign: 'center',
            verticalAlign: 'top',
            type: 'success'
          });

          // 跳转到仪表盘
          setTimeout(() => {
            this.$router.push('/dashboard');
          }, 500);
        }
      } catch (error) {
        console.error('登录失败:', error);
        
        if (error.response) {
          // 服务器返回错误
          if (error.response.status === 401) {
            this.errorMessage = '用户名或密码错误';
          } else if (error.response.status === 403) {
            this.errorMessage = '您没有管理员权限';
          } else {
            this.errorMessage = error.response.data.detail || '登录失败，请稍后重试';
          }
        } else if (error.request) {
          // 请求发送但没有收到响应
          this.errorMessage = '无法连接到服务器，请检查网络';
        } else {
          // 其他错误
          this.errorMessage = '登录失败，请稍后重试';
        }

        this.$notify({
          message: this.errorMessage,
          icon: 'error',
          horizontalAlign: 'center',
          verticalAlign: 'top',
          type: 'danger'
        });
      } finally {
        this.loading = false;
      }
    },

    /**
     * 保存凭据
     */
    saveCredentials() {
      const credentials = {
        username: this.loginForm.username,
        password: this.loginForm.password
      };
      localStorage.setItem('admin_credentials', JSON.stringify(credentials));
    },

    /**
     * 加载保存的凭据
     */
    loadSavedCredentials() {
      const saved = localStorage.getItem('admin_credentials');
      if (saved) {
        try {
          const credentials = JSON.parse(saved);
          this.loginForm.username = credentials.username;
          this.loginForm.password = credentials.password;
          this.loginForm.rememberMe = true;
        } catch (e) {
          console.error('加载保存的凭据失败:', e);
        }
      }
    },

    /**
     * 清除保存的凭据
     */
    clearSavedCredentials() {
      localStorage.removeItem('admin_credentials');
    }
  }
};
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e0f2f1;
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
  background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%);
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
  background: linear-gradient(135deg, #388e3c 0%, #4caf50 100%);
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
  box-shadow: 0 15px 50px rgba(76, 175, 80, 0.15);
  overflow: hidden;
  min-height: 500px;
}

/* 左侧信息面板 */
.info-panel {
  flex: 1;
  background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%);
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

.feature-item .md-icon {
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

.login-form .md-field {
  margin-bottom: 20px;
}

.form-options {
  display: flex;
  justify-content: flex-start;
  margin: 10px 0 20px 0;
}

.login-button {
  width: 100%;
  height: 45px;
  font-size: 16px;
  font-weight: 600;
  margin-top: 10px;
  position: relative;
}

.login-button .spinner {
  display: inline-block;
  vertical-align: middle;
}

.error-message {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 15px;
  padding: 10px;
  background: #ffebee;
  border-radius: 4px;
  color: #c62828;
  font-size: 14px;
}

.error-message .md-icon {
  margin-right: 8px;
  font-size: 20px;
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

