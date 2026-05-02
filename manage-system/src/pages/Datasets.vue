<template>
  <div class="content">
    <div class="md-layout">
      <!-- 页面标题和操作按钮 -->
      <div class="md-layout-item md-size-100">
        <md-card>
          <md-card-header data-background-color="blue">
            <h4 class="title">数据集仓库</h4>
            <p class="category">管理 GraphRAG 数据源文件，支持查看元数据、导入/导出</p>
          </md-card-header>
          <md-card-content>
            <div class="actions-bar">
              <md-button class="md-raised md-primary" @click="showUploadDialog = true">
                <md-icon>cloud_upload</md-icon>
                上传文件
              </md-button>
              <md-button class="md-raised md-success" @click="importAllToNeo4j">
                <md-icon>backup</md-icon>
                一键导入到 Neo4j
              </md-button>
              <md-button class="md-raised" @click="refreshDatasets">
                <md-icon>refresh</md-icon>
                刷新列表
              </md-button>
            </div>
          </md-card-content>
        </md-card>
      </div>

      <!-- 数据集列表 -->
      <div class="md-layout-item md-size-100">
        <md-card>
          <md-card-header data-background-color="green">
            <h4 class="title">数据集列表</h4>
            <p class="category">共 {{ totalItems }} 个文件</p>
          </md-card-header>
          <md-card-content>
            <md-progress-bar v-if="loading" md-mode="indeterminate"></md-progress-bar>
            <md-table v-else v-model="datasets" md-sort="filename" md-sort-order="asc" md-card>
              <md-table-row slot="md-table-row" slot-scope="{ item }">
                <md-table-cell md-label="文件名" md-sort-by="filename">
                  <md-icon>{{ getFileIcon(item.file_type) }}</md-icon>
                  {{ item.filename }}
                </md-table-cell>
                <md-table-cell md-label="类型" md-sort-by="file_type">
                  <md-chip :class="item.file_type === 'parquet' ? 'md-primary' : 'md-accent'">
                    {{ item.file_type.toUpperCase() }}
                  </md-chip>
                </md-table-cell>
                <md-table-cell md-label="大小" md-sort-by="file_size">
                  {{ formatFileSize(item.file_size) }}
                </md-table-cell>
                <md-table-cell md-label="行数" md-sort-by="row_count">
                  {{ item.row_count.toLocaleString() }}
                </md-table-cell>
                <md-table-cell md-label="列数" md-sort-by="column_count">
                  {{ item.column_count }}
                </md-table-cell>
                <md-table-cell md-label="更新时间" md-sort-by="updated_at">
                  {{ formatDate(item.updated_at) }}
                </md-table-cell>
                <md-table-cell md-label="操作">
                  <md-button class="md-just-icon md-simple md-primary" @click="previewDataset(item)">
                    <md-icon>visibility</md-icon>
                    <md-tooltip md-direction="top">预览</md-tooltip>
                  </md-button>
                  <md-button class="md-just-icon md-simple md-info" @click="downloadDataset(item)">
                    <md-icon>download</md-icon>
                    <md-tooltip md-direction="top">下载</md-tooltip>
                  </md-button>
                  <md-button class="md-just-icon md-simple md-success" @click="importSingleDataset(item)">
                    <md-icon>cloud_upload</md-icon>
                    <md-tooltip md-direction="top">导入到 Neo4j</md-tooltip>
                  </md-button>
                  <md-button class="md-just-icon md-simple md-danger" @click="confirmDelete(item)">
                    <md-icon>delete</md-icon>
                    <md-tooltip md-direction="top">删除</md-tooltip>
                  </md-button>
                </md-table-cell>
              </md-table-row>
            </md-table>
            
            <!-- 分页组件 -->
            <div v-if="totalPages > 1" class="pagination-container">
              <md-button
                class="md-icon-button"
                :disabled="currentPage === 1"
                @click="handlePageChange(currentPage - 1)"
              >
                <md-icon>chevron_left</md-icon>
              </md-button>
              
              <md-button
                v-for="page in visiblePages"
                :key="page"
                class="md-raised"
                :class="{ 'md-primary': page === currentPage }"
                @click="handlePageChange(page)"
              >
                {{ page }}
              </md-button>
              
              <md-button
                class="md-icon-button"
                :disabled="currentPage === totalPages"
                @click="handlePageChange(currentPage + 1)"
              >
                <md-icon>chevron_right</md-icon>
              </md-button>
              
              <span class="pagination-info">
                共 {{ totalItems }} 条，第 {{ currentPage }}/{{ totalPages }} 页
              </span>
            </div>
          </md-card-content>
        </md-card>
      </div>
    </div>

    <!-- 上传对话框 -->
    <md-dialog :md-active.sync="showUploadDialog">
      <md-dialog-title>上传数据集文件</md-dialog-title>
      <md-dialog-content>
        <p>请选择 CSV 或 Parquet 文件上传</p>
        <input type="file" ref="fileInput" @change="handleFileSelect" accept=".csv,.parquet" />
        <div v-if="selectedFile" class="file-info">
          <md-icon>insert_drive_file</md-icon>
          <span>{{ selectedFile.name }}</span>
          <span>({{ formatFileSize(selectedFile.size) }})</span>
        </div>
      </md-dialog-content>
      <md-dialog-actions>
        <md-button class="md-primary" @click="showUploadDialog = false">取消</md-button>
        <md-button class="md-primary md-raised" @click="uploadFile" :disabled="!selectedFile || uploading">
          {{ uploading ? "上传中..." : "上传" }}
        </md-button>
      </md-dialog-actions>
    </md-dialog>

    <!-- 预览对话框 -->
    <md-dialog :md-active.sync="showPreviewDialog" class="preview-dialog">
      <md-dialog-title>{{ previewData.filename }}</md-dialog-title>
      <md-dialog-content>
        <div v-if="loadingPreview" style="text-align: center; padding: 20px">
          <md-progress-spinner md-mode="indeterminate"></md-progress-spinner>
        </div>
        <div v-else>
          <p><strong>列名:</strong> {{ previewData.columns ? previewData.columns.join(", ") : "" }}</p>
          <div class="table-container">
            <table class="preview-table">
              <thead>
                <tr>
                  <th v-for="col in previewData.columns" :key="col">{{ col }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in previewData.data" :key="idx">
                  <td v-for="col in previewData.columns" :key="col">
                    {{ row[col] }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </md-dialog-content>
      <md-dialog-actions>
        <md-button class="md-primary" @click="showPreviewDialog = false">关闭</md-button>
      </md-dialog-actions>
    </md-dialog>

    <!-- 删除确认对话框 -->
    <md-dialog-confirm
      :md-active.sync="showDeleteDialog"
      md-title="确认删除"
      :md-content="`确定要删除文件 ${datasetToDelete ? datasetToDelete.filename : ''} 吗？此操作不可恢复！`"
      md-confirm-text="删除"
      md-cancel-text="取消"
      @md-confirm="deleteDataset"
    />
  </div>
</template>

<script>
import datasetsApi from "@/api/datasets";

export default {
  name: "Datasets",
  computed: {
    visiblePages() {
      const pages = [];
      const maxVisible = 5;
      let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
      let end = Math.min(this.totalPages, start + maxVisible - 1);
      
      if (end - start < maxVisible - 1) {
        start = Math.max(1, end - maxVisible + 1);
      }
      
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
      return pages;
    },
  },
  data() {
    return {
      datasets: [],
      loading: false,
      showUploadDialog: false,
      showPreviewDialog: false,
      showDeleteDialog: false,
      selectedFile: null,
      uploading: false,
      previewData: {
        filename: "",
        columns: [],
        data: [],
      },
      loadingPreview: false,
      datasetToDelete: null,
      importStatusInterval: null,
      // 分页相关
      currentPage: 1,
      pageSize: 10,
      totalItems: 0,
      totalPages: 0,
    };
  },
  mounted() {
    this.loadDatasets();
  },
  beforeDestroy() {
    if (this.importStatusInterval) {
      clearInterval(this.importStatusInterval);
    }
  },
  methods: {
    async loadDatasets() {
      this.loading = true;
      try {
        const response = await datasetsApi.getDatasets(this.currentPage, this.pageSize);
        this.datasets = response.items || [];
        this.totalItems = response.total || 0;
        this.totalPages = response.total_pages || 0;
        this.currentPage = response.page || 1;
      } catch (error) {
        console.error("加载数据集列表失败:", error);
        this.notifyError("加载数据集列表失败");
      } finally {
        this.loading = false;
      }
    },

    handlePageChange(page) {
      this.currentPage = page;
      this.loadDatasets();
    },

    refreshDatasets() {
      this.loadDatasets();
    },

    getFileIcon(fileType) {
      return fileType === "parquet" ? "table_chart" : "description";
    },

    formatFileSize(bytes) {
      if (bytes < 1024) return bytes + " B";
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB";
      if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + " MB";
      return (bytes / (1024 * 1024 * 1024)).toFixed(2) + " GB";
    },

    formatDate(isoString) {
      const date = new Date(isoString);
      return date.toLocaleString("zh-CN");
    },

    handleFileSelect(event) {
      const file = event.target.files[0];
      if (file) {
        // 检查文件类型
        if (!file.name.endsWith(".csv") && !file.name.endsWith(".parquet")) {
          this.notifyError("只支持 CSV 和 Parquet 文件");
          return;
        }
        this.selectedFile = file;
      }
    },

    async uploadFile() {
      if (!this.selectedFile) return;

      this.uploading = true;
      try {
        await datasetsApi.uploadDataset(this.selectedFile);
        this.notifySuccess("文件上传成功");
        this.showUploadDialog = false;
        this.selectedFile = null;
        if (this.$refs.fileInput) {
          this.$refs.fileInput.value = "";
        }
        // 立即刷新列表
        await this.loadDatasets();
      } catch (error) {
        console.error("上传文件失败:", error);
        this.notifyError("上传文件失败");
      } finally {
        this.uploading = false;
      }
    },

    async previewDataset(dataset) {
      this.showPreviewDialog = true;
      this.loadingPreview = true;
      try {
        this.previewData = await datasetsApi.previewDataset(dataset.filename, 10);
      } catch (error) {
        console.error("预览数据失败:", error);
        this.notifyError("预览数据失败");
      } finally {
        this.loadingPreview = false;
      }
    },

    async downloadDataset(dataset) {
      try {
        const response = await datasetsApi.downloadDataset(dataset.filename);
        const url = window.URL.createObjectURL(new Blob([response]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", dataset.filename);
        document.body.appendChild(link);
        link.click();
        link.remove();
        this.notifySuccess("文件下载成功");
      } catch (error) {
        console.error("下载文件失败:", error);
        this.notifyError("下载文件失败");
      }
    },

    confirmDelete(dataset) {
      this.datasetToDelete = dataset;
      this.showDeleteDialog = true;
    },

    async deleteDataset() {
      if (!this.datasetToDelete) return;

      try {
        await datasetsApi.deleteDataset(this.datasetToDelete.filename);
        this.notifySuccess("文件删除成功");
        await this.loadDatasets();
      } catch (error) {
        console.error("删除文件失败:", error);
        this.notifyError("删除文件失败");
      } finally {
        this.datasetToDelete = null;
      }
    },

    async importSingleDataset(dataset) {
      try {
        const result = await datasetsApi.importToNeo4j(dataset.filename, false);
        this.notifyInfo(`正在导入 ${dataset.filename} 到 Neo4j...`);
        this.startPollingImportStatus();
      } catch (error) {
        console.error("导入失败:", error);
        this.notifyError("导入失败");
      }
    },

    async importAllToNeo4j() {
      if (!confirm("确定要导入所有数据集到 Neo4j 吗？这可能需要几分钟时间。")) {
        return;
      }

      try {
        await datasetsApi.importAllToNeo4j(true);
        this.notifyInfo("正在导入所有数据集到 Neo4j，请稍候...");
        this.startPollingImportStatus();
      } catch (error) {
        console.error("导入失败:", error);
        this.notifyError("导入失败");
      }
    },

    startPollingImportStatus() {
      // 每3秒轮询一次导入状态
      if (this.importStatusInterval) {
        clearInterval(this.importStatusInterval);
      }

      this.importStatusInterval = setInterval(async () => {
        try {
          const status = await datasetsApi.getImportStatus();
          if (status.status === "success") {
            clearInterval(this.importStatusInterval);
            this.notifySuccess("知识图谱已更新");
          } else if (status.status === "error") {
            clearInterval(this.importStatusInterval);
            this.notifyError(`导入失败: ${status.message}`);
          }
        } catch (error) {
          console.error("获取导入状态失败:", error);
        }
      }, 3000);
    },

    notifySuccess(message) {
      this.$notify({
        message: message,
        icon: "add_alert",
        horizontalAlign: "center",
        verticalAlign: "top",
        type: "success",
      });
    },

    notifyError(message) {
      this.$notify({
        message: message,
        icon: "add_alert",
        horizontalAlign: "center",
        verticalAlign: "top",
        type: "danger",
      });
    },

    notifyInfo(message) {
      this.$notify({
        message: message,
        icon: "add_alert",
        horizontalAlign: "center",
        verticalAlign: "top",
        type: "info",
      });
    },
  },
};
</script>

<style scoped>
.actions-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.preview-dialog {
  max-width: 90vw;
}

.table-container {
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.preview-table th,
.preview-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.preview-table th {
  background-color: #4caf50;
  color: white;
  font-weight: bold;
  position: sticky;
  top: 0;
  z-index: 10;
}

.preview-table tr:nth-child(even) {
  background-color: #f9f9f9;
}

.preview-table tr:hover {
  background-color: #f1f1f1;
}

/* 分页样式 */
.pagination-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  margin-top: 20px;
  padding: 10px;
}

.pagination-info {
  margin-left: 15px;
  color: #666;
  font-size: 14px;
}
</style>

