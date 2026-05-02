/**
 * 数据集仓库管理 API
 */
import http from "./http";

export default {
  /**
   * 获取所有数据集列表（支持分页）
   * @param {number} page - 页码
   * @param {number} pageSize - 每页数量
   */
  getDatasets(page = 1, pageSize = 10) {
    return http.get("/api/v1/admin/datasets", {
      params: { page, page_size: pageSize },
    });
  },

  /**
   * 获取单个数据集的详细元数据
   * @param {string} filename - 文件名
   */
  getDatasetMetadata(filename) {
    return http.get(`/api/v1/admin/datasets/${filename}`);
  },

  /**
   * 预览数据集内容
   * @param {string} filename - 文件名
   * @param {number} rows - 预览行数
   */
  previewDataset(filename, rows = 10) {
    return http.get(`/api/v1/admin/datasets/${filename}/preview`, {
      params: { rows },
    });
  },

  /**
   * 下载数据集文件
   * @param {string} filename - 文件名
   */
  downloadDataset(filename) {
    return http.get(`/api/v1/admin/datasets/${filename}/download`, {
      responseType: "blob",
    });
  },

  /**
   * 上传数据集文件
   * @param {File} file - 文件对象
   */
  uploadDataset(file) {
    const formData = new FormData();
    formData.append("file", file);
    return http.post("/api/v1/admin/datasets/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },

  /**
   * 删除数据集文件
   * @param {string} filename - 文件名
   */
  deleteDataset(filename) {
    return http.delete(`/api/v1/admin/datasets/${filename}`);
  },

  /**
   * 导入数据集到 Neo4j
   * @param {string} filename - 文件名
   * @param {boolean} clearExisting - 是否清空现有数据
   */
  importToNeo4j(filename, clearExisting = true) {
    return http.post("/api/v1/admin/datasets/import-to-neo4j", {
      filename,
      clear_existing: clearExisting,
    });
  },

  /**
   * 导入所有数据集到 Neo4j
   * @param {boolean} clearExisting - 是否清空现有数据
   */
  importAllToNeo4j(clearExisting = true) {
    return http.post("/api/v1/admin/datasets/import-all-to-neo4j", null, {
      params: { clear_existing: clearExisting },
    });
  },

  /**
   * 获取导入状态
   */
  getImportStatus() {
    return http.get("/api/v1/admin/datasets/import-status");
  },
};

