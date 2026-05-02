<template>
  <div class="content">
    <div class="md-layout">
      <div class="md-layout-item md-medium-size-100 md-xsmall-size-100 md-size-100">
        <md-card>
          <md-card-header data-background-color="green">
            <h4 class="title">用户管理</h4>
            <p class="category">管理系统所有用户</p>
          </md-card-header>
          <md-card-content>
            <!-- 搜索和操作栏 -->
            <div class="md-layout md-gutter" style="margin-bottom: 20px">
              <div class="md-layout-item md-size-50">
                <md-field>
                  <label>搜索用户</label>
                  <md-input v-model="searchQuery" @input="handleSearch"></md-input>
                </md-field>
              </div>
              <div class="md-layout-item md-size-50" style="text-align: right; padding-top: 20px">
                <md-button class="md-raised md-success" @click="showCreateDialog">
                  <md-icon>add</md-icon>
                  新增用户
                </md-button>
              </div>
            </div>

            <!-- 用户表格 -->
            <md-table v-model="users" :table-header-color="tableHeaderColor">
              <md-table-row slot="md-table-row" slot-scope="{ item }">
                <md-table-cell md-label="ID">{{ item.id }}</md-table-cell>
                <md-table-cell md-label="邮箱">{{ item.email }}</md-table-cell>
                <md-table-cell md-label="角色">
                  <md-chip :class="getRoleClass(item.role)">{{ item.role }}</md-chip>
                </md-table-cell>
                <md-table-cell md-label="创建时间">{{ formatDate(item.created_at) }}</md-table-cell>
                <md-table-cell md-label="操作">
                  <md-button class="md-just-icon md-simple md-primary" @click="viewConversations(item.id)">
                    <md-icon>chat</md-icon>
                    <md-tooltip md-direction="top">查看对话</md-tooltip>
                  </md-button>
                  <md-button class="md-just-icon md-simple md-warning" @click="showEditDialog(item)">
                    <md-icon>edit</md-icon>
                    <md-tooltip md-direction="top">编辑</md-tooltip>
                  </md-button>
                  <md-button class="md-just-icon md-simple md-danger" @click="confirmDelete(item)">
                    <md-icon>delete</md-icon>
                    <md-tooltip md-direction="top">删除</md-tooltip>
                  </md-button>
                </md-table-cell>
              </md-table-row>
            </md-table>

            <!-- 分页 -->
            <div class="pagination" style="text-align: center; margin-top: 20px">
              <md-button class="md-icon-button" @click="prevPage" :disabled="currentPage === 1">
                <md-icon>chevron_left</md-icon>
              </md-button>
              <span style="margin: 0 20px">第 {{ currentPage }} / {{ totalPages }} 页</span>
              <md-button class="md-icon-button" @click="nextPage" :disabled="currentPage >= totalPages">
                <md-icon>chevron_right</md-icon>
              </md-button>
            </div>
          </md-card-content>
        </md-card>
      </div>
    </div>

    <!-- 创建/编辑用户对话框 -->
    <md-dialog :md-active.sync="showDialog">
      <md-dialog-title>{{ isEdit ? "编辑用户" : "新增用户" }}</md-dialog-title>
      <md-dialog-content>
        <md-field>
          <label>邮箱</label>
          <md-input v-model="formData.email" type="email" required></md-input>
        </md-field>
        <md-field v-if="!isEdit">
          <label>密码</label>
          <md-input v-model="formData.password" type="password" required></md-input>
        </md-field>
        <md-field>
          <label>角色</label>
          <md-select v-model="formData.role">
            <md-option value="user">普通用户</md-option>
            <md-option value="admin">管理员</md-option>
          </md-select>
        </md-field>
      </md-dialog-content>
      <md-dialog-actions>
        <md-button class="md-primary" @click="showDialog = false">取消</md-button>
        <md-button class="md-primary md-raised" @click="saveUser">保存</md-button>
      </md-dialog-actions>
    </md-dialog>

    <!-- 删除确认对话框 -->
    <md-dialog-confirm
      :md-active.sync="showDeleteDialog"
      md-title="确认删除"
      :md-content="`确定要删除用户 <strong>${deleteTarget?.username}</strong> 吗？此操作不可恢复。`"
      md-confirm-text="删除"
      md-cancel-text="取消"
      @md-confirm="deleteUser"
    />

    <!-- 对话历史对话框 -->
    <md-dialog :md-active.sync="showConversationsDialog" class="conversations-dialog" :md-fullscreen="false">
      <md-dialog-title>
        用户对话历史 (ID: {{ selectedUserId }})
        <md-button class="md-icon-button md-accent" @click="exportConversations" style="float: right">
          <md-icon>download</md-icon>
          <md-tooltip>导出为文件</md-tooltip>
        </md-button>
      </md-dialog-title>
      <md-dialog-content>
        <!-- 加载状态 -->
        <div v-if="conversationsLoading" style="text-align: center; padding: 40px">
          <md-progress-spinner md-mode="indeterminate"></md-progress-spinner>
          <p>加载中...</p>
        </div>

        <!-- 对话列表 -->
        <div v-else-if="conversations.length > 0" class="conversations-list">
          <md-card v-for="conv in conversations" :key="conv.id" class="conversation-card">
            <md-card-header class="conversation-header">
              <div class="header-content">
                <div class="header-title">
                  <md-icon>question_answer</md-icon>
                  <span>对话 #{{ conv.id }}</span>
                </div>
                <div class="header-time">
                  <md-icon style="font-size: 16px">access_time</md-icon>
                  <span>{{ formatDate(conv.created_at) }}</span>
                </div>
              </div>
            </md-card-header>
            <md-card-content>
              <div class="message-block question-block">
                <div class="message-label">
                  <md-icon style="font-size: 18px">person</md-icon>
                  <strong>用户提问：</strong>
                </div>
                <div class="message-content">{{ conv.question }}</div>
              </div>
              <md-divider style="margin: 12px 0"></md-divider>
              <div class="message-block answer-block">
                <div class="message-label">
                  <md-icon style="font-size: 18px">smart_toy</md-icon>
                  <strong>AI 回答：</strong>
                </div>
                <div class="message-content">{{ conv.answer }}</div>
              </div>
            </md-card-content>
          </md-card>
        </div>

        <!-- 空状态 -->
        <div v-else style="text-align: center; padding: 40px">
          <md-icon style="font-size: 64px; color: #999">chat_bubble_outline</md-icon>
          <p style="color: #999; margin-top: 20px">暂无对话记录</p>
        </div>
      </md-dialog-content>
      <md-dialog-actions>
        <md-button class="md-primary" @click="showConversationsDialog = false">关闭</md-button>
      </md-dialog-actions>
    </md-dialog>
  </div>
</template>

<script>
import usersApi from "@/api/users";
import conversationsApi from "@/api/conversations";

export default {
  name: "Users",
  data() {
    return {
      users: [],
      searchQuery: "",
      currentPage: 1,
      pageSize: 10,
      totalPages: 1,
      totalCount: 0,
      tableHeaderColor: "green",
      showDialog: false,
      showDeleteDialog: false,
      showConversationsDialog: false,
      isEdit: false,
      formData: {
        username: "",
        email: "",
        password: "",
        role: "user",
      },
      deleteTarget: null,
      // 对话历史相关
      selectedUserId: null,
      conversations: [],
      conversationsLoading: false,
    };
  },
  mounted() {
    this.loadUsers();
  },
  methods: {
    async loadUsers() {
      try {
        const response = await usersApi.getUsers(this.currentPage, this.pageSize, this.searchQuery);
        this.users = response.items || [];
        this.totalCount = response.total || 0;
        this.totalPages = Math.ceil(this.totalCount / this.pageSize);
      } catch (error) {
        this.$notify({
          message: "加载用户列表失败: " + error,
          icon: "error",
          horizontalAlign: "right",
          verticalAlign: "top",
          type: "danger",
        });
      }
    },
    handleSearch() {
      this.currentPage = 1;
      this.loadUsers();
    },
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
        this.loadUsers();
      }
    },
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
        this.loadUsers();
      }
    },
    showCreateDialog() {
      this.isEdit = false;
      this.formData = { email: "", password: "", role: "user" };
      this.showDialog = true;
    },
    showEditDialog(user) {
      this.isEdit = true;
      this.formData = {
        id: user.id,
        email: user.email,
        role: user.role,
      };
      this.showDialog = true;
    },
    async saveUser() {
      try {
        if (this.isEdit) {
          await usersApi.updateUser(this.formData.id, this.formData);
          this.$notify({
            message: "用户更新成功",
            icon: "check",
            horizontalAlign: "right",
            verticalAlign: "top",
            type: "success",
          });
        } else {
          await usersApi.createUser(this.formData);
          this.$notify({
            message: "用户创建成功",
            icon: "check",
            horizontalAlign: "right",
            verticalAlign: "top",
            type: "success",
          });
        }
        this.showDialog = false;
        this.loadUsers();
      } catch (error) {
        this.$notify({
          message: "操作失败: " + error,
          icon: "error",
          horizontalAlign: "right",
          verticalAlign: "top",
          type: "danger",
        });
      }
    },
    confirmDelete(user) {
      this.deleteTarget = user;
      this.showDeleteDialog = true;
    },
    async deleteUser() {
      try {
        await usersApi.deleteUser(this.deleteTarget.id);
        this.$notify({
          message: "用户删除成功",
          icon: "check",
          horizontalAlign: "right",
          verticalAlign: "top",
          type: "success",
        });
        this.loadUsers();
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
    async viewConversations(userId) {
      this.selectedUserId = userId;
      this.showConversationsDialog = true;
      this.conversations = [];
      this.conversationsLoading = true;
      
      try {
        const response = await conversationsApi.exportConversations(userId);
        this.conversations = response.items || [];
      } catch (error) {
        this.$notify({
          message: "加载对话历史失败: " + error,
          icon: "error",
          horizontalAlign: "right",
          verticalAlign: "top",
          type: "danger",
        });
      } finally {
        this.conversationsLoading = false;
      }
    },
    async exportConversations() {
      try {
        const response = await conversationsApi.exportConversations(this.selectedUserId);
        
        // 创建文件内容
        let fileContent = `用户对话历史导出\n`;
        fileContent += `用户 ID: ${this.selectedUserId}\n`;
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
        link.download = `用户${this.selectedUserId}_对话历史_${new Date().toISOString().slice(0, 10)}.txt`;
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
    getRoleClass(role) {
      return role === "admin" ? "md-primary" : "md-accent";
    },
    formatDate(dateString) {
      if (!dateString) return "-";
      return new Date(dateString).toLocaleString("zh-CN");
    },
  },
};
</script>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 对话历史对话框样式 */
.conversations-dialog {
  max-width: 900px !important;
  max-height: 80vh !important;
}

/* 强制对话框居中 */
.conversations-dialog >>> .md-dialog-container {
  max-width: 900px !important;
  width: 90% !important;
  max-height: 85vh !important;
  position: fixed !important;
  left: 50% !important;
  top: 50% !important;
  transform: translate(-50%, -50%) !important;
  margin: 0 !important;
}

.conversations-dialog >>> .md-dialog-content {
  max-height: calc(85vh - 150px) !important;
  overflow-y: auto !important;
}

.conversations-list {
  max-height: 500px;
  overflow-y: auto;
  padding: 8px;
}

.conversation-card {
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 对话卡片头部样式 */
.conversation-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: white !important;
  padding: 12px 16px !important;
}

.conversation-header .header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.conversation-header .header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
}

.conversation-header .header-title .md-icon {
  color: white !important;
}

.conversation-header .header-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  opacity: 0.9;
}

.conversation-header .header-time .md-icon {
  color: white !important;
}

.message-block {
  margin: 8px 0;
}

.message-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: #666;
  font-size: 14px;
}

.message-content {
  padding: 12px;
  background-color: #f5f5f5;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 14px;
  line-height: 1.6;
}

.question-block .message-content {
  background-color: #e3f2fd;
  border-left: 3px solid #2196f3;
}

.answer-block .message-content {
  background-color: #f1f8e9;
  border-left: 3px solid #8bc34a;
}
</style>

