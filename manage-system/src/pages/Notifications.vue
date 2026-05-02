<template>
  <div class="content">
    <div class="md-layout">
      <!-- 统计卡片 -->
      <div class="md-layout-item md-medium-size-100 md-xsmall-size-100 md-size-33">
        <stats-card data-background-color="blue">
          <template slot="header">
            <md-icon>notifications</md-icon>
          </template>

          <template slot="content">
            <p class="category">总通知数</p>
            <h3 class="title">{{ stats.total }}</h3>
          </template>
        </stats-card>
      </div>

      <div class="md-layout-item md-medium-size-100 md-xsmall-size-100 md-size-33">
        <stats-card data-background-color="orange">
          <template slot="header">
            <md-icon>mark_email_unread</md-icon>
          </template>

          <template slot="content">
            <p class="category">未读通知</p>
            <h3 class="title">{{ stats.unread }}</h3>
          </template>
        </stats-card>
      </div>

      <div class="md-layout-item md-medium-size-100 md-xsmall-size-100 md-size-33">
        <stats-card data-background-color="green">
          <template slot="header">
            <md-icon>today</md-icon>
          </template>

          <template slot="content">
            <p class="category">今日通知</p>
            <h3 class="title">{{ stats.today }}</h3>
          </template>
        </stats-card>
      </div>

      <!-- 通知列表 -->
      <div class="md-layout-item md-size-100">
        <md-card>
          <md-card-header data-background-color="green">
            <div style="display: flex; justify-content: space-between; align-items: center">
              <div>
                <h4 class="title">通知列表</h4>
                <p class="category">系统操作通知记录</p>
              </div>
              <div>
                <md-button class="md-raised md-info" @click="markAllAsRead" :disabled="stats.unread === 0">
                  <md-icon>done_all</md-icon>
                  全部已读
                </md-button>
                <md-button class="md-raised" @click="filterUnread = !filterUnread">
                  <md-icon>{{ filterUnread ? 'mail' : 'drafts' }}</md-icon>
                  {{ filterUnread ? '显示全部' : '仅未读' }}
                </md-button>
              </div>
            </div>
          </md-card-header>

          <md-card-content>
            <div v-if="loading" style="text-align: center; padding: 40px">
              <md-progress-spinner md-mode="indeterminate"></md-progress-spinner>
              <p>加载中...</p>
            </div>

            <div v-else-if="notifications.length === 0" style="text-align: center; padding: 40px; color: #999">
              <md-icon style="font-size: 64px">notifications_none</md-icon>
              <p>暂无通知</p>
            </div>

            <div v-else class="notifications-list">
              <div
                v-for="notification in notifications"
                :key="notification.id"
                class="notification-item"
                :class="[
                  `level-${notification.level}`,
                  { 'unread': !notification.is_read }
                ]"
              >
                <div class="notification-icon">
                  <md-icon>{{ getNotificationIcon(notification.type) }}</md-icon>
                </div>
                
                <div class="notification-content">
                  <div class="notification-header">
                    <h4>{{ notification.title }}</h4>
                    <span class="notification-time">{{ formatTime(notification.created_at) }}</span>
                  </div>
                  <p class="notification-message">{{ notification.message }}</p>
                  <div class="notification-meta">
                    <span v-if="notification.username" class="notification-user">
                      <md-icon>person</md-icon>
                      {{ notification.username }}
                    </span>
                    <span class="notification-type">
                      <md-icon>label</md-icon>
                      {{ getNotificationTypeLabel(notification.type) }}
                    </span>
                  </div>
                </div>

                <div class="notification-actions">
                  <md-button
                    :class="[
                      'md-icon-button md-dense',
                      notification.is_read ? 'read-button' : 'md-primary'
                    ]"
                    @click="markAsRead(notification.id)"
                    :title="notification.is_read ? '已读' : '标记已读'"
                    :disabled="notification.is_read"
                  >
                    <md-icon>{{ notification.is_read ? 'done_all' : 'done' }}</md-icon>
                  </md-button>
                  <md-button
                    class="md-icon-button md-dense md-accent"
                    @click="deleteNotification(notification.id)"
                    title="删除"
                  >
                    <md-icon>delete</md-icon>
                  </md-button>
                </div>
              </div>
            </div>

            <!-- 分页控件 -->
            <div v-if="totalPages > 1" class="pagination">
              <md-button
                class="md-icon-button"
                @click="handlePageChange(currentPage - 1)"
                :disabled="currentPage === 1"
              >
                <md-icon>chevron_left</md-icon>
              </md-button>

              <md-button
                v-for="page in visiblePages"
                :key="page"
                class="md-icon-button"
                :class="{ 'md-raised md-primary': page === currentPage }"
                @click="handlePageChange(page)"
              >
                {{ page }}
              </md-button>

              <md-button
                class="md-icon-button"
                @click="handlePageChange(currentPage + 1)"
                :disabled="currentPage === totalPages"
              >
                <md-icon>chevron_right</md-icon>
              </md-button>

              <span style="margin-left: 16px; color: #999">
                第 {{ currentPage }} / {{ totalPages }} 页，共 {{ totalItems }} 条
              </span>
            </div>
          </md-card-content>
        </md-card>
      </div>
    </div>
  </div>
</template>

<script>
import notificationsApi from "@/api/notifications";
import { StatsCard } from "@/components";

export default {
  name: "Notifications",
  components: {
    StatsCard,
  },
  data() {
    return {
      loading: false,
      notifications: [],
      stats: {
        total: 0,
        unread: 0,
        today: 0,
      },
      currentPage: 1,
      pageSize: 20,
      totalItems: 0,
      totalPages: 0,
      filterUnread: false,
    };
  },
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
  mounted() {
    this.loadNotifications();
    this.loadStats();
  },
  watch: {
    filterUnread() {
      this.currentPage = 1;
      this.loadNotifications();
    },
  },
  methods: {
    async loadNotifications() {
      this.loading = true;
      try {
        const response = await notificationsApi.getNotifications(
          this.currentPage,
          this.pageSize,
          this.filterUnread ? false : null
        );
        this.notifications = response.items || [];
        this.totalItems = response.total || 0;
        this.totalPages = response.total_pages || 0;
        this.currentPage = response.page || 1;
      } catch (error) {
        console.error("加载通知列表失败:", error);
        this.notifyError("加载通知列表失败");
      } finally {
        this.loading = false;
      }
    },
    async loadStats() {
      try {
        const stats = await notificationsApi.getNotificationStats();
        this.stats = stats;
      } catch (error) {
        console.error("加载通知统计失败:", error);
      }
    },
    async markAsRead(notificationId) {
      try {
        await notificationsApi.markAsRead(notificationId);
        this.notifySuccess("已标记为已读");
        await this.loadNotifications();
        await this.loadStats();
      } catch (error) {
        console.error("标记已读失败:", error);
        this.notifyError("标记已读失败");
      }
    },
    async markAllAsRead() {
      try {
        await notificationsApi.markAllAsRead();
        this.notifySuccess("已全部标记为已读");
        await this.loadNotifications();
        await this.loadStats();
      } catch (error) {
        console.error("全部标记已读失败:", error);
        this.notifyError("全部标记已读失败");
      }
    },
    async deleteNotification(notificationId) {
      if (!confirm("确定要删除这条通知吗？")) {
        return;
      }
      try {
        await notificationsApi.deleteNotification(notificationId);
        this.notifySuccess("通知已删除");
        await this.loadNotifications();
        await this.loadStats();
      } catch (error) {
        console.error("删除通知失败:", error);
        this.notifyError("删除通知失败");
      }
    },
    handlePageChange(page) {
      this.currentPage = page;
      this.loadNotifications();
    },
    getNotificationIcon(type) {
      const icons = {
        login: "login",
        logout: "logout",
        password_change: "lock",
        export: "download",
        import: "upload",
        system: "info",
      };
      return icons[type] || "notifications";
    },
    getNotificationTypeLabel(type) {
      const labels = {
        login: "登录",
        logout: "登出",
        password_change: "密码修改",
        export: "数据导出",
        import: "数据导入",
        system: "系统通知",
      };
      return labels[type] || type;
    },
    formatTime(dateStr) {
      const date = new Date(dateStr);
      const now = new Date();
      const diff = now - date;

      // 小于1分钟
      if (diff < 60000) {
        return "刚刚";
      }
      // 小于1小时
      if (diff < 3600000) {
        return `${Math.floor(diff / 60000)}分钟前`;
      }
      // 小于1天
      if (diff < 86400000) {
        return `${Math.floor(diff / 3600000)}小时前`;
      }
      // 小于7天
      if (diff < 604800000) {
        return `${Math.floor(diff / 86400000)}天前`;
      }
      // 显示具体日期
      return date.toLocaleString("zh-CN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
    },
    notifySuccess(message) {
      this.$notify({
        message: message,
        icon: "check_circle",
        horizontalAlign: "center",
        verticalAlign: "top",
        type: "success",
      });
    },
    notifyError(message) {
      this.$notify({
        message: message,
        icon: "error",
        horizontalAlign: "center",
        verticalAlign: "top",
        type: "danger",
      });
    },
  },
};
</script>

<style scoped>
.notifications-list {
  margin-top: 20px;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  margin-bottom: 12px;
  border-radius: 8px;
  border-left: 4px solid #999;
  background-color: #f9f9f9;
  transition: all 0.3s ease;
}

.notification-item.unread {
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.notification-item.level-success {
  border-left-color: #4caf50;
}

.notification-item.level-info {
  border-left-color: #2196f3;
}

.notification-item.level-warning {
  border-left-color: #ff9800;
}

.notification-item.level-danger {
  border-left-color: #f44336;
}

.notification-icon {
  flex-shrink: 0;
  margin-right: 16px;
}

.notification-icon .md-icon {
  font-size: 32px;
  color: #666;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.notification-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.notification-time {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
}

.notification-message {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #666;
  line-height: 1.5;
}

.notification-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #999;
}

.notification-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.notification-meta .md-icon {
  font-size: 16px;
}

.notification-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
  margin-left: 16px;
}

/* 已读按钮样式 */
.notification-actions .md-primary {
  background-color: #4caf50 !important;
  color: white !important;
}

.notification-actions .md-primary:hover {
  background-color: #45a049 !important;
}

.notification-actions .read-button {
  background-color: #e0e0e0 !important;
  color: #999 !important;
  cursor: default !important;
}

.notification-actions .read-button:hover {
  background-color: #e0e0e0 !important;
}

.notification-actions .read-button .md-icon {
  color: #999 !important;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.pagination .md-button {
  margin: 0 4px;
}
</style>
