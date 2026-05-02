/**
 * 用户管理 API
 */
import http from "./http";

export default {
  /**
   * 获取用户列表（分页）
   * @param {number} page - 页码
   * @param {number} size - 每页数量
   * @param {string} search - 搜索关键词
   */
  getUsers(page = 1, size = 10, search = "") {
    return http.get("/api/v1/admin/users", {
      params: { page, size, search },
    });
  },

  /**
   * 获取单个用户详情
   * @param {number} userId
   */
  getUserById(userId) {
    return http.get(`/api/v1/admin/users/${userId}`);
  },

  /**
   * 创建用户
   * @param {object} userData - { username, email, password, role }
   */
  createUser(userData) {
    return http.post("/api/v1/admin/users", userData);
  },

  /**
   * 更新用户
   * @param {number} userId
   * @param {object} userData
   */
  updateUser(userId, userData) {
    return http.put(`/api/v1/admin/users/${userId}`, userData);
  },

  /**
   * 删除用户
   * @param {number} userId
   */
  deleteUser(userId) {
    return http.delete(`/api/v1/admin/users/${userId}`);
  },
};

