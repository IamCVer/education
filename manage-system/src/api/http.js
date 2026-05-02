/**
 * Axios HTTP 客户端配置
 */
import axios from "axios";

// 根据环境变量或默认值设置 API 基础 URL
const baseURL = process.env.VUE_APP_API_BASE_URL || "http://localhost:8000";

const http = axios.create({
  baseURL: baseURL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 请求拦截器：添加 Token
http.interceptors.request.use(
  (config) => {
    // 尝试获取管理员 token 或普通用户 token
    const token = localStorage.getItem("admin_token") || localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器：统一错误处理
http.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      console.log('HTTP Error:', { status, data, url: error.config.url });
      
      if (status === 401) {
        // Token 过期或无效，跳转登录
        console.log('401 Unauthorized - clearing tokens and redirecting to login');
        localStorage.removeItem("admin_token");
        localStorage.removeItem("access_token");
        localStorage.removeItem("admin_user");
        
        // 使用 Vue Router 进行跳转（如果可用），否则使用 window.location
        if (window.vueRouter) {
          window.vueRouter.push('/login');
        } else {
          window.location.href = "/#/login";
        }
      }
      return Promise.reject(data || error.message);
    }
    return Promise.reject(error.message || "Network Error");
  }
);

export default http;

