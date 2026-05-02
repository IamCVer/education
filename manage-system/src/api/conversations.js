/**
 * 对话历史 API
 */
import http from "./http";

export default {
  /**
   * 获取用户的对话历史（分页）
   * @param {number} userId
   * @param {number} page
   * @param {number} size
   */
  getConversations(userId, page = 1, size = 20) {
    return http.get("/api/v1/admin/conversations", {
      params: { user_id: userId, page, size },
    });
  },

  /**
   * 获取单条对话详情
   * @param {number} conversationId
   */
  getConversationById(conversationId) {
    return http.get(`/api/v1/admin/conversations/${conversationId}`);
  },

  /**
   * 删除对话记录
   * @param {number} conversationId
   */
  deleteConversation(conversationId) {
    return http.delete(`/api/v1/admin/conversations/${conversationId}`);
  },

  /**
   * 导出用户对话历史（获取所有对话，不分页）
   * @param {number} userId
   */
  exportConversations(userId) {
    return http.get(`/api/v1/admin/conversations`, {
      params: { user_id: userId, page: 1, size: 10000, is_export: true }, // 获取大量记录用于导出，标记为导出操作
    });
  },
};

