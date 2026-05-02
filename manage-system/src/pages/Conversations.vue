<template>
  <div class="content">
    <div class="md-layout">
      <div class="md-layout-item md-medium-size-100 md-xsmall-size-100 md-size-100">
        <md-card>
          <md-card-header data-background-color="blue">
            <h4 class="title">用户对话历史</h4>
            <p class="category">用户 ID: {{ userId }}</p>
          </md-card-header>
          <md-card-content>
            <!-- 返回按钮 -->
            <div style="margin-bottom: 20px">
              <md-button class="md-raised" @click="goBack">
                <md-icon>arrow_back</md-icon>
                返回用户列表
              </md-button>
              <md-button class="md-raised md-primary" @click="loadConversations">
                <md-icon>refresh</md-icon>
                刷新
              </md-button>
              <md-button class="md-raised md-accent" @click="exportToFile">
                <md-icon>download</md-icon>
                导出为文件
              </md-button>
            </div>

            <!-- 加载状态 -->
            <div v-if="loading" style="text-align: center; padding: 40px">
              <md-progress-spinner md-mode="indeterminate"></md-progress-spinner>
              <p>加载中...</p>
            </div>

            <!-- 对话列表 -->
            <div v-else-if="conversations.length > 0" class="conversations-list">
              <md-card v-for="conv in conversations" :key="conv.id" class="conversation-card">
                <md-card-header>
                  <div class="md-title">
                    <md-icon class="conversation-icon">question_answer</md-icon>
                    对话 #{{ conv.id }}
                  </div>
                  <div class="md-subhead">{{ formatDate(conv.created_at) }}</div>
                </md-card-header>
                <md-card-content>
                  <div class="message-block question-block">
                    <div class="message-label">
                      <md-icon>person</md-icon>
                      <strong>用户提问：</strong>
                    </div>
                    <div class="message-content">{{ conv.question }}</div>
                  </div>
                  <md-divider></md-divider>
                  <div class="message-block answer-block">
                    <div class="message-label">
                      <md-icon>smart_toy</md-icon>
                      <strong>AI 回答：</strong>
                    </div>
                    <div class="message-content">{{ conv.answer }}</div>
                  </div>
                  <div v-if="conv.context" class="context-info">
                    <md-chip class="md-primary">上下文长度: {{ conv.context.length }}</md-chip>
                  </div>
                </md-card-content>
                <md-card-actions>
                  <md-button class="md-icon-button md-accent" @click="viewDetails(conv)">
                    <md-icon>visibility</md-icon>
                    <md-tooltip>查看详情</md-tooltip>
                  </md-button>
                  <md-button class="md-icon-button md-accent" @click="confirmDelete(conv)">
                    <md-icon>delete</md-icon>
                    <md-tooltip>删除</md-tooltip>
                  </md-button>
                </md-card-actions>
              </md-card>
            </div>

            <!-- 空状态 -->
            <div v-else style="text-align: center; padding: 40px">
              <md-icon style="font-size: 64px; color: #999">chat_bubble_outline</md-icon>
              <p style="color: #999; margin-top: 20px">暂无对话记录</p>
            </div>

            <!-- 分页 -->
            <div v-if="totalPages > 1" class="pagination">
              <md-button class="md-icon-button" @click="prevPage" :disabled="currentPage === 1">
                <md-icon>chevron_left</md-icon>
              </md-button>
              <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
              <md-button class="md-icon-button" @click="nextPage" :disabled="currentPage >= totalPages">
                <md-icon>chevron_right</md-icon>
              </md-button>
            </div>
          </md-card-content>
        </md-card>
      </div>
    </div>

    <!-- 详情对话框 -->
    <md-dialog :md-active.sync="showDetailsDialog" class="details-dialog">
      <md-dialog-title>对话详情</md-dialog-title>
      <md-dialog-content v-if="selectedConv">
        <div class="detail-section">
          <h4>基本信息</h4>
          <p><strong>对话 ID:</strong> {{ selectedConv.id }}</p>
          <p><strong>用户 ID:</strong> {{ selectedConv.user_id }}</p>
          <p><strong>创建时间:</strong> {{ formatDate(selectedConv.created_at) }}</p>
        </div>
        <md-divider></md-divider>
        <div class="detail-section">
          <h4>问题</h4>
          <p>{{ selectedConv.question }}</p>
        </div>
        <md-divider></md-divider>
        <div class="detail-section">
          <h4>回答</h4>
          <p>{{ selectedConv.answer }}</p>
        </div>
        <div v-if="selectedConv.context" class="detail-section">
          <md-divider></md-divider>
          <h4>上下文</h4>
          <pre>{{ JSON.stringify(selectedConv.context, null, 2) }}</pre>
        </div>
      </md-dialog-content>
      <md-dialog-actions>
        <md-button class="md-primary" @click="showDetailsDialog = false">关闭</md-button>
      </md-dialog-actions>
    </md-dialog>

    <!-- 删除确认 -->
    <md-dialog-confirm
      :md-active.sync="showDeleteDialog"
      md-title="确认删除"
      md-content="确定要删除这条对话记录吗？"
      md-confirm-text="删除"
      md-cancel-text="取消"
      @md-confirm="deleteConversation"
    />
  </div>
</template>

<script>
import conversationsApi from "@/api/conversations";

export default {
  name: "Conversations",
  props: {
    userId: {
      type: [String, Number],
      required: true,
    },
  },
  data() {
    return {
      conversations: [],
      loading: false,
      currentPage: 1,
      pageSize: 10,
      totalPages: 1,
      totalCount: 0,
      showDetailsDialog: false,
      showDeleteDialog: false,
      selectedConv: null,
      deleteTarget: null,
    };
  },
  mounted() {
    this.loadConversations();
  },
  methods: {
    async loadConversations() {
      this.loading = true;
      try {
        const response = await conversationsApi.getConversations(this.userId, this.currentPage, this.pageSize);
        this.conversations = response.items || [];
        this.totalCount = response.total || 0;
        this.totalPages = Math.ceil(this.totalCount / this.pageSize);
      } catch (error) {
        this.$notify({
          message: "加载对话历史失败: " + error,
          icon: "error",
          horizontalAlign: "right",
          verticalAlign: "top",
          type: "danger",
        });
      } finally {
        this.loading = false;
      }
    },
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
        this.loadConversations();
      }
    },
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
        this.loadConversations();
      }
    },
    viewDetails(conv) {
      this.selectedConv = conv;
      this.showDetailsDialog = true;
    },
    confirmDelete(conv) {
      this.deleteTarget = conv;
      this.showDeleteDialog = true;
    },
    async deleteConversation() {
      try {
        await conversationsApi.deleteConversation(this.deleteTarget.id);
        this.$notify({
          message: "对话删除成功",
          icon: "check",
          horizontalAlign: "right",
          verticalAlign: "top",
          type: "success",
        });
        this.loadConversations();
      } catch (error) {
        this.$notify({
          message: "删除失败: " + error,
          icon: "error",
          horizontalAlign: "right",
          verticalAlign: "top",
          type: "danger",
        });
      }
    },
    goBack() {
      this.$router.push({ name: "Users" });
    },
    formatDate(dateString) {
      if (!dateString) return "-";
      return new Date(dateString).toLocaleString("zh-CN");
    },
    async exportToFile() {
      try {
        // 导出所有对话（不分页）
        const response = await conversationsApi.exportConversations(this.userId);
        
        // 创建文件内容
        let fileContent = `用户对话历史导出\n`;
        fileContent += `用户 ID: ${this.userId}\n`;
        fileContent += `导出时间: ${new Date().toLocaleString("zh-CN")}\n`;
        fileContent += `总对话数: ${response.items ? response.items.length : 0}\n`;
        fileContent += `${"=".repeat(80)}\n\n`;
        
        if (response.items && response.items.length > 0) {
          response.items.forEach((conv, index) => {
            fileContent += `【对话 ${index + 1}】\n`;
            fileContent += `ID: ${conv.id}\n`;
            fileContent += `时间: ${this.formatDate(conv.created_at)}\n`;
            fileContent += `\n【用户提问】\n${conv.question}\n`;
            fileContent += `\n【AI 回答】\n${conv.answer}\n`;
            if (conv.context) {
              fileContent += `\n【上下文信息】\n${JSON.stringify(conv.context, null, 2)}\n`;
            }
            fileContent += `\n${"-".repeat(80)}\n\n`;
          });
        } else {
          fileContent += "暂无对话记录\n";
        }
        
        // 创建并下载文件
        const blob = new Blob([fileContent], { type: "text/plain;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `用户${this.userId}_对话历史_${new Date().toISOString().slice(0, 10)}.txt`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        this.$notify({
          message: "对话历史导出成功",
          icon: "check",
          horizontalAlign: "right",
          verticalAlign: "top",
          type: "success",
        });
      } catch (error) {
        this.$notify({
          message: "导出失败: " + error,
          icon: "error",
          horizontalAlign: "right",
          verticalAlign: "top",
          type: "danger",
        });
      }
    },
  },
};
</script>

<style scoped>
.conversations-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.conversation-card {
  margin-bottom: 0;
}

.conversation-icon {
  vertical-align: middle;
  margin-right: 8px;
}

.message-block {
  margin: 16px 0;
}

.message-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: #666;
}

.message-content {
  padding: 12px;
  background-color: #f5f5f5;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.question-block .message-content {
  background-color: #e3f2fd;
}

.answer-block .message-content {
  background-color: #f1f8e9;
}

.context-info {
  margin-top: 12px;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 20px;
}

.details-dialog {
  max-width: 800px;
}

.detail-section {
  margin: 16px 0;
}

.detail-section h4 {
  margin-bottom: 8px;
  color: #333;
}

.detail-section pre {
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
}
</style>

