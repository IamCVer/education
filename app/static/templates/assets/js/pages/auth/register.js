// 注册页面逻辑
class RegisterPage {
    constructor() {
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.initFormValidation();
    }
    
    bindEvents() {
        // 绑定表单提交事件
        document.getElementById('registerForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegister();
        });
        
        // 绑定返回登录链接
        const backToLoginLink = document.querySelector('a[href="/login"]');
        if (backToLoginLink) {
            backToLoginLink.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.href = '/pages/auth/login.html';
            });
        }
        
        // 实时密码强度检查
        const passwordInput = document.getElementById('register-password');
        if (passwordInput) {
            passwordInput.addEventListener('input', (e) => {
                this.checkPasswordStrength(e.target.value);
            });
        }
        
        // 实时邮箱验证
        const emailInput = document.getElementById('register-email');
        if (emailInput) {
            emailInput.addEventListener('blur', (e) => {
                this.validateEmail(e.target.value);
            });
        }
    }
    
    initFormValidation() {
        // 初始化表单验证规则
        this.validationRules = {
            email: {
                required: true,
                email: true,
                minlength: 5,
                maxlength: 100
            },
            password: {
                required: true,
                minlength: 8,
                maxlength: 50
            },
            confirmPassword: {
                required: true,
                equalTo: '#register-password'
            },
            role: {
                required: false
            }
        };
    }
    
    async handleRegister() {
        const email = document.getElementById('register-email').value.trim();
        const password = document.getElementById('register-password').value;
        const confirmPassword = document.getElementById('register-confirm-password').value;
        const role = document.getElementById('register-role').value || 'student';
        
        // 表单验证
        if (!this.validateForm(email, password, confirmPassword)) {
            return;
        }
        
        this.showLoading(true);
        this.hideAlerts();
        
        try {
            const response = await window.authService.register(email, password, role);
            
            if (response.id) {
                this.showSuccess('注册成功！正在跳转到登录页面...');
                setTimeout(() => {
                    window.location.href = '/pages/auth/login.html';
                }, 2000);
            } else {
                this.showError(response.detail || '注册失败');
            }
        } catch (error) {
            console.error('注册失败:', error);
            this.showError(error.message || '注册失败，请检查网络连接');
        } finally {
            this.showLoading(false);
        }
    }
    
    validateForm(email, password, confirmPassword) {
        // 验证邮箱
        if (!email) {
            this.showError('请输入邮箱地址');
            return false;
        }
        
        if (!window.Utils.isValidEmail(email)) {
            this.showError('请输入有效的邮箱地址');
            return false;
        }
        
        // 验证密码
        if (!password) {
            this.showError('请输入密码');
            return false;
        }
        
        const passwordValidation = window.Utils.validatePassword(password);
        if (!passwordValidation.isValid) {
            this.showError('密码必须至少8位，包含大小写字母和数字');
            return false;
        }
        
        // 验证确认密码
        if (!confirmPassword) {
            this.showError('请确认密码');
            return false;
        }
        
        if (password !== confirmPassword) {
            this.showError('两次输入的密码不一致');
            return false;
        }
        
        return true;
    }
    
    validateEmail(email) {
        const emailInput = document.getElementById('register-email');
        const emailFeedback = document.getElementById('email-feedback');
        
        if (!email) {
            this.updateFieldValidation(emailInput, false, '请输入邮箱地址');
            return false;
        }
        
        if (!window.Utils.isValidEmail(email)) {
            this.updateFieldValidation(emailInput, false, '请输入有效的邮箱地址');
            return false;
        }
        
        this.updateFieldValidation(emailInput, true, '邮箱格式正确');
        return true;
    }
    
    checkPasswordStrength(password) {
        const passwordInput = document.getElementById('register-password');
        const strengthIndicator = document.getElementById('password-strength');
        
        if (!password) {
            this.updatePasswordStrength(strengthIndicator, 0, '');
            return;
        }
        
        const validation = window.Utils.validatePassword(password);
        let strength = 0;
        let message = '';
        
        if (validation.length) strength += 25;
        if (validation.lowerCase) strength += 25;
        if (validation.upperCase) strength += 25;
        if (validation.numbers) strength += 25;
        
        if (strength < 50) {
            message = '弱';
        } else if (strength < 75) {
            message = '中等';
        } else {
            message = '强';
        }
        
        this.updatePasswordStrength(strengthIndicator, strength, message);
    }
    
    updateFieldValidation(field, isValid, message) {
        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
        }
        
        const feedback = field.parentNode.querySelector('.invalid-feedback, .valid-feedback');
        if (feedback) {
            feedback.textContent = message;
        }
    }
    
    updatePasswordStrength(indicator, strength, message) {
        if (!indicator) return;
        
        const progressBar = indicator.querySelector('.progress-bar');
        const strengthText = indicator.querySelector('.strength-text');
        
        if (progressBar) {
            progressBar.style.width = strength + '%';
            
            if (strength < 50) {
                progressBar.className = 'progress-bar bg-danger';
            } else if (strength < 75) {
                progressBar.className = 'progress-bar bg-warning';
            } else {
                progressBar.className = 'progress-bar bg-success';
            }
        }
        
        if (strengthText) {
            strengthText.textContent = message;
        }
    }
    
    showLoading(show) {
        const loadingEl = document.querySelector('.loading');
        const normalEl = document.querySelector('.normal');
        const registerBtn = document.getElementById('registerBtn');
        
        if (show) {
            if (loadingEl) loadingEl.style.display = 'inline';
            if (normalEl) normalEl.style.display = 'none';
            if (registerBtn) registerBtn.disabled = true;
        } else {
            if (loadingEl) loadingEl.style.display = 'none';
            if (normalEl) normalEl.style.display = 'inline';
            if (registerBtn) registerBtn.disabled = false;
        }
    }
    
    showSuccess(message) {
        const successAlert = document.getElementById('successAlert');
        const successMessage = document.getElementById('successMessage');
        
        if (successAlert && successMessage) {
            successMessage.textContent = message;
            successAlert.style.display = 'block';
            document.getElementById('errorAlert').style.display = 'none';
        } else if (window.Utils) {
            window.Utils.showSuccess(message);
        }
    }
    
    showError(message) {
        const errorAlert = document.getElementById('errorAlert');
        const errorMessage = document.getElementById('errorMessage');
        
        if (errorAlert && errorMessage) {
            errorMessage.textContent = message;
            errorAlert.style.display = 'block';
            document.getElementById('successAlert').style.display = 'none';
        } else if (window.Utils) {
            window.Utils.showError(message);
        }
    }
    
    hideAlerts() {
        const successAlert = document.getElementById('successAlert');
        const errorAlert = document.getElementById('errorAlert');
        
        if (successAlert) successAlert.style.display = 'none';
        if (errorAlert) errorAlert.style.display = 'none';
    }
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    window.registerPage = new RegisterPage();
});
