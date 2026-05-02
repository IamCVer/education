<template>
  <div class="content">
    <div class="md-layout">
      <div class="md-layout-item md-medium-size-100 md-xsmall-size-100 md-size-100">
        <md-card>
          <md-card-header data-background-color="blue">
            <h4 class="title">Docker 容器日志监控</h4>
            <p class="category">实时查看容器日志输出</p>
          </md-card-header>
          <md-card-content>
            <!-- 服务选择器 -->
            <div class="controls">
              <md-field>
                <label>选择服务</label>
                <md-select v-model="selectedService" @md-selected="switchService">
                  <md-option value="frontend">Frontend</md-option>
                  <md-option value="backend">Backend</md-option>
                  <md-option value="chattts">ChatTTS</md-option>
                  <md-option value="worker">Worker</md-option>
                </md-select>
              </md-field>

              <md-chip :class="isConnected ? 'md-primary' : 'md-accent'">
                <md-icon>{{ isConnected ? "wifi" : "wifi_off" }}</md-icon>
                {{ isConnected ? "实时连接" : "已断开" }}
              </md-chip>

              <md-button class="md-raised md-primary" @click="toggleConnection">
                <md-icon>{{ isConnected ? "pause" : "play_arrow" }}</md-icon>
                {{ isConnected ? "暂停" : "开始" }}
              </md-button>

              <md-button class="md-raised" @click="clearLogs">
                <md-icon>clear</md-icon>
                清空日志
              </md-button>

              <md-button class="md-raised md-accent" @click="downloadLogs">
                <md-icon>download</md-icon>
                下载日志
              </md-button>
            </div>

            <!-- 日志显示区域 -->
            <div class="log-container" ref="logContainer">
              <pre class="log-content">{{ logsText }}</pre>
            </div>

            <!-- 统计信息 -->
            <div class="log-stats">
              <md-chip class="md-primary">总行数: {{ logLines.length }}</md-chip>
              <md-chip class="md-accent">错误: {{ errorCount }}</md-chip>
              <md-chip>警告: {{ warningCount }}</md-chip>
            </div>
          </md-card-content>
        </md-card>
      </div>
    </div>
  </div>
</template>

<script>
import socketService from "@/plugins/socket";
import logsApi from "@/api/logs";

export default {
  name: "Logs",
  data() {
    return {
      selectedService: "backend",
      logLines: [],
      maxLines: 500, // 最多保留 500 行
      isConnected: false,
      errorCount: 0,
      warningCount: 0,
    };
  },
  computed: {
    logsText() {
      return this.logLines.join("\n");
    },
  },
  mounted() {
    this.loadInitialLogs();
    this.connectWebSocket();
  },
  beforeDestroy() {
    this.disconnectWebSocket();
  },
  methods: {
    async loadInitialLogs() {
      try {
        const response = await logsApi.getServiceLogs(this.selectedService, 50);
        if (response && response.logs) {
          this.logLines = response.logs.split("\n").filter((line) => line.trim());
          this.updateStats();
          this.scrollToBottom();
        }
      } catch (error) {
        console.error("加载初始日志失败:", error);
      }
    },
    connectWebSocket() {
      if (!socketService.isConnected()) {
        socketService.connect();
      }
      const channel = `logs_${this.selectedService}`;
      socketService.subscribe(channel, this.handleLogData);
      this.isConnected = true;
    },
    disconnectWebSocket() {
      const channel = `logs_${this.selectedService}`;
      socketService.unsubscribe(channel);
      this.isConnected = false;
    },
    handleLogData(data) {
      if (data && data.line) {
        this.addLogLine(data.line);
      }
    },
    addLogLine(line) {
      this.logLines.push(line);

      // 限制行数
      if (this.logLines.length > this.maxLines) {
        this.logLines.shift();
      }

      this.updateStats();
      this.$nextTick(() => {
        this.scrollToBottom();
      });
    },
    updateStats() {
      this.errorCount = this.logLines.filter((line) =>
        /error|exception|failed|fatal/i.test(line)
      ).length;
      this.warningCount = this.logLines.filter((line) => /warning|warn/i.test(line)).length;
    },
    scrollToBottom() {
      const container = this.$refs.logContainer;
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    },
    switchService() {
      this.disconnectWebSocket();
      this.logLines = [];
      this.errorCount = 0;
      this.warningCount = 0;
      this.loadInitialLogs();
      this.connectWebSocket();
    },
    toggleConnection() {
      if (this.isConnected) {
        this.disconnectWebSocket();
      } else {
        this.connectWebSocket();
      }
    },
    clearLogs() {
      this.logLines = [];
      this.errorCount = 0;
      this.warningCount = 0;
    },
    downloadLogs() {
      const blob = new Blob([this.logsText], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${this.selectedService}_logs_${new Date().toISOString()}.txt`;
      a.click();
      URL.revokeObjectURL(url);
    },
  },
};
</script>

<style scoped>
.controls {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.controls .md-field {
  min-width: 200px;
  margin: 0;
}

.log-container {
  background-color: #1e1e1e;
  border-radius: 4px;
  padding: 16px;
  height: 500px;
  overflow-y: auto;
  font-family: "Courier New", Courier, monospace;
}

.log-content {
  color: #d4d4d4;
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.log-stats {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

/* 滚动条样式 */
.log-container::-webkit-scrollbar {
  width: 8px;
}

.log-container::-webkit-scrollbar-track {
  background: #2d2d2d;
}

.log-container::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.log-container::-webkit-scrollbar-thumb:hover {
  background: #777;
}
</style>

