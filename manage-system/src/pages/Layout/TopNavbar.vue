<template>
  <md-toolbar md-elevation="0" class="md-transparent">
    <div class="md-toolbar-row">
      <div class="md-toolbar-section-start">
        <h3 class="md-title">{{ $route.name }}</h3>
      </div>
      <div class="md-toolbar-section-end">
        <md-button
          class="md-just-icon md-simple md-toolbar-toggle"
          :class="{ toggled: $sidebar.showSidebar }"
          @click="toggleSidebar"
        >
          <span class="icon-bar"></span>
          <span class="icon-bar"></span>
          <span class="icon-bar"></span>
        </md-button>

        <div class="md-collapse">
          <div class="md-autocomplete">
            <md-autocomplete
              class="search"
              v-model="selectedEmployee"
              :md-options="employees"
            >
              <label>搜索...</label>
            </md-autocomplete>
          </div>
          <md-list>
            <md-list-item href="#/">
              <i class="material-icons">dashboard</i>
              <p class="hidden-lg hidden-md">仪表盘</p>
            </md-list-item>

            <!-- <md-list-item href="#/notifications" class="dropdown">
              <drop-down>
                <a slot="title" class="dropdown-toggle" data-toggle="dropdown">
                  <i class="material-icons">notifications</i>
                  <span class="notification">5</span>
                  <p class="hidden-lg hidden-md">Notifications</p>
                </a>
                <ul class="dropdown-menu dropdown-menu-right">
                  <li><a href="#">Mike John responded to your email</a></li>
                  <li><a href="#">You have 5 new tasks</a></li>
                  <li><a href="#">You're now friend with Andrew</a></li>
                  <li><a href="#">Another Notification</a></li>
                  <li><a href="#">Another One</a></li>
                </ul>
              </drop-down>
            </md-list-item> -->

            <li class="md-list-item">
              <a
                href="#/notifications"
                class="md-list-item-router md-list-item-container md-button-clean dropdown"
              >
                <div class="md-list-item-content">
                  <drop-down>
                    <md-button
                      slot="title"
                      class="md-button md-just-icon md-simple"
                      data-toggle="dropdown"
                    >
                      <md-icon>notifications</md-icon>
                      <span v-if="unreadCount > 0" class="notification">{{ unreadCount }}</span>
                      <p class="hidden-lg hidden-md">通知</p>
                    </md-button>
                    <ul class="dropdown-menu dropdown-menu-right">
                      <li v-if="recentNotifications.length === 0" class="notification-empty">
                        <a href="#" style="color: #999">暂无未读通知</a>
                      </li>
                      <li 
                        v-for="notification in recentNotifications" 
                        :key="notification.id"
                        @click="handleNotificationClick(notification.id)"
                      >
                        <a href="#">
                          <strong>{{ notification.title }}</strong>
                          <br>
                          <small style="color: #999">{{ formatNotificationTime(notification.created_at) }}</small>
                        </a>
                      </li>
                      <li class="divider" v-if="recentNotifications.length > 0"></li>
                      <li v-if="recentNotifications.length > 0">
                        <a href="#/notifications" style="text-align: center; font-weight: bold">
                          查看全部通知
                        </a>
                      </li>
                    </ul>
                  </drop-down>
                </div>
              </a>
            </li>

            <md-list-item href="#/user">
              <i class="material-icons">person</i>
              <p class="hidden-lg hidden-md">关于我们</p>
            </md-list-item>

            <md-list-item @click="handleLogout">
              <i class="material-icons">exit_to_app</i>
              <p class="hidden-lg hidden-md">退出登录</p>
            </md-list-item>
          </md-list>
        </div>
      </div>
    </div>
  </md-toolbar>
</template>

<script>
import notificationsApi from "@/api/notifications";

export default {
  data() {
    return {
      selectedEmployee: null,
      employees: [
        "Jim Halpert",
        "Dwight Schrute",
        "Michael Scott",
        "Pam Beesly",
        "Angela Martin",
        "Kelly Kapoor",
        "Ryan Howard",
        "Kevin Malone",
      ],
      unreadCount: 0,
      recentNotifications: [],
      pollingInterval: null,
    };
  },
  mounted() {
    this.loadNotificationStats();
    this.loadRecentNotifications();
    
    // 每30秒轮询一次通知
    this.pollingInterval = setInterval(() => {
      this.loadNotificationStats();
      this.loadRecentNotifications();
    }, 30000);
  },
  beforeDestroy() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
  },
  methods: {
    toggleSidebar() {
      this.$sidebar.displaySidebar(!this.$sidebar.showSidebar);
    },
    async loadNotificationStats() {
      try {
        const stats = await notificationsApi.getNotificationStats();
        this.unreadCount = stats.unread || 0;
      } catch (error) {
        console.error("加载通知统计失败:", error);
      }
    },
    async loadRecentNotifications() {
      try {
        const response = await notificationsApi.getNotifications(1, 5, false);
        this.recentNotifications = response.items || [];
      } catch (error) {
        console.error("加载最新通知失败:", error);
      }
    },
    formatNotificationTime(dateStr) {
      const date = new Date(dateStr);
      const now = new Date();
      const diff = now - date;

      if (diff < 60000) return "刚刚";
      if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
      if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
      return `${Math.floor(diff / 86400000)}天前`;
    },
    async handleNotificationClick(notificationId) {
      try {
        await notificationsApi.markAsRead(notificationId);
        await this.loadNotificationStats();
        await this.loadRecentNotifications();
      } catch (error) {
        console.error("标记已读失败:", error);
      }
    },
    handleLogout() {
      // 清除 token 和用户信息
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_user');
      
      // 显示通知
      this.$notify({
        message: '已退出登录',
        icon: 'check_circle',
        horizontalAlign: 'center',
        verticalAlign: 'top',
        type: 'info'
      });

      // 跳转到登录页
      this.$router.push('/login');
    }
  },
};
</script>

<style lang="css"></style>
