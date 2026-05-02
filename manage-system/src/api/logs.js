/**
 * 日志相关 API（主要通过 WebSocket）
 */
import http from "./http";

export default {
  /**
   * 获取可用的服务列表
   */
  getServices() {
    return http.get("/api/v1/logs/services");
  },

  /**
   * 获取服务的历史日志（HTTP 方式，用于初始加载）
   * @param {string} service - 服务名称（frontend/backend/chattts/worker）
   * @param {number} lines - 行数
   */
  getServiceLogs(service, lines = 50) {
    return http.get(`/api/v1/logs/${service}`, {
      params: { lines },
    });
  },
};

