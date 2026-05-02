/**
 * 统计数据 API
 */
import http from "./http";

export default {
  /**
   * 获取 GPU 显存利用率（首次加载）
   */
  getGpuMetrics() {
    return http.get("/api/v1/stats/gpu-metrics");
  },

  /**
   * 获取实体排行数据（Degree Top10 & Frequency Top10）
   */
  getEntitiesRanking() {
    return http.get("/api/v1/stats/entities");
  },

  /**
   * 获取社区层级树（旭日图数据）
   */
  getCommunityTree() {
    return http.get("/api/v1/stats/community-tree");
  },

  /**
   * 获取力导向图数据（节点和边）
   */
  getForceGraph() {
    return http.get("/api/v1/stats/force-graph");
  },

  /**
   * 刷新统计数据缓存（管理员操作）
   */
  refreshStats() {
    return http.post("/api/v1/stats/refresh");
  },
};

