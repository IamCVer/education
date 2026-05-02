/**
 * 通知管理 API
 */
import http from "./http";

export default {
  /**
   * 获取通知列表
   * @param {number} page - 页码
   * @param {number} pageSize - 每页数量
   * @param {boolean} isRead - 筛选已读/未读
   */
  getNotifications(page = 1, pageSize = 20, isRead = null) {
    const params = { page, page_size: pageSize };
    if (isRead !== null) {
      params.is_read = isRead;
    }
    return http.get("/api/v1/notifications", { params });
  },

  /**
   * 获取通知统计
   */
  getNotificationStats() {
    return http.get("/api/v1/notifications/stats");
  },

  /**
   * 标记单个通知为已读
   * @param {number} notificationId - 通知ID
   */
  markAsRead(notificationId) {
    return http.put(`/api/v1/notifications/${notificationId}/read`);
  },

  /**
   * 标记所有通知为已读
   */
  markAllAsRead() {
    return http.put("/api/v1/notifications/read-all");
  },

  /**
   * 删除通知
   * @param {number} notificationId - 通知ID
   */
  deleteNotification(notificationId) {
    return http.delete(`/api/v1/notifications/${notificationId}`);
  },
};

