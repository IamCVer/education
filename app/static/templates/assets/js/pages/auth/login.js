// 登录页面逻辑 (最终修正版)
class LoginPage {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadSavedCredentials();
    }

    bindEvents() {
        $('#loginForm').on('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });
        $('#check1').on('change', () => {
            this.toggleRememberMe();
        });
        $('.register-link').on('click', () => {
            window.location.href = '/pages/auth/register.html';
        });
        $('.forgot-password').on('click', () => {
            this.showForgotPassword();
        });
    }

    async handleLogin() {
        const username = $('#login-username').val().trim();
        const password = $('#login-password').val();
        const rememberMe = $('#check1').is(':checked');

        if (!this.validateForm(username, password)) {
            return;
        }

        this.showLoading(true);
        this.hideAlerts();

        try {
            // authService.login 应该直接返回后端传来的JSON数据
            const responseData = await window.authService.login(username, password);

            // vvvvvvvvvvvv 【最终修正】 vvvvvvvvvvvv
            // 修正判断条件：不再检查 response.success，
            // 而是检查后端实际返回的 access_token 是否存在。
            if (responseData && responseData.access_token) {
            // ^^^^^^^^^^^^ 【最终修正】 ^^^^^^^^^^^^

                // 保存用户信息
                // 注意：这里我们直接使用 responseData.access_token
                window.authService.saveUserInfo(responseData.access_token, username, rememberMe ? password : null);

                // 显示成功消息
                window.Utils.showSuccess('登录成功，正在跳转...');

                // 延迟跳转
                setTimeout(() => {
                    window.location.href = '/pages/dashboard/chat.html';
                }, 1000);
            } else {
                // 如果后端返回的数据中没有 access_token，则认为登录失败
                window.Utils.showError(responseData.message || '登录失败，用户名或密码错误');
            }
        } catch (error) {
            console.error('登录错误:', error);
            window.Utils.showError('登录失败，请检查网络连接');
        } finally {
            this.showLoading(false);
        }
    }

    validateForm(username, password) {
        let isValid = true;
        if (!username) {
            this.updateFieldValidation('#login-username', false, '请输入用户名');
            isValid = false;
        } else if (!window.Utils.isValidEmail(username)) {
            this.updateFieldValidation('#login-username', false, '请输入有效的邮箱地址');
            isValid = false;
        } else {
            this.updateFieldValidation('#login-username', true);
        }
        if (!password) {
            this.updateFieldValidation('#login-password', false, '请输入密码');
            isValid = false;
        } else {
            this.updateFieldValidation('#login-password', true);
        }
        return isValid;
    }

    updateFieldValidation(field, isValid, message = '') {
        const $field = $(field);
        const $formGroup = $field.closest('.form-group');
        if (isValid) {
            $field.removeClass('is-invalid').addClass('is-valid');
            $formGroup.find('.invalid-feedback').hide();
        } else {
            $field.removeClass('is-valid').addClass('is-invalid');
            $formGroup.find('.invalid-feedback').text(message).show();
        }
    }

    loadSavedCredentials() {
        const savedCredentials = window.authService.loadSavedCredentials();
        if (savedCredentials) {
            $('#login-username').val(savedCredentials.username);
            $('#login-password').val(savedCredentials.password);
            $('#check1').prop('checked', true);
        }
    }

    toggleRememberMe() {
        const rememberMe = $('#check1').is(':checked');
        if (!rememberMe) {
            localStorage.removeItem('savedPassword');
        }
    }

    showForgotPassword() {
        window.Utils.showInfo('请联系管理员重置密码');
    }

    showLoading(show) {
        if (show) {
            $('#loginBtn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> 登录中...');
        } else {
            $('#loginBtn').prop('disabled', false).html('登录');
        }
    }

    hideAlerts() {
        $('.alert').hide();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.loginPage = new LoginPage();
});