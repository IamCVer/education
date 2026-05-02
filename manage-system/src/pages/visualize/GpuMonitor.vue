<template>
  <div class="content">
    <div class="md-layout">
      <div class="md-layout-item md-medium-size-100 md-xsmall-size-100 md-size-100">
        <md-card>
          <md-card-header data-background-color="orange">
            <h4 class="title">GPU 显存监控</h4>
            <p class="category">实时监控 GPU 显存利用率</p>
          </md-card-header>
          <md-card-content>
            <!-- 状态指示器 -->
            <div class="status-bar">
              <md-chip :class="isConnected ? 'md-primary' : 'md-accent'">
                <md-icon>{{ isConnected ? "wifi" : "wifi_off" }}</md-icon>
                {{ isConnected ? "实时连接" : "已断开" }}
              </md-chip>
              <md-chip v-if="latestMetric" class="md-primary">
                当前使用: {{ latestMetric.used }} MB / {{ latestMetric.total }} MB ({{
                  latestMetric.percentage
                }}%)
              </md-chip>
            </div>

            <!-- 图表容器 -->
            <div class="chart-container">
              <canvas ref="chartCanvas"></canvas>
            </div>

            <!-- 控制按钮 -->
            <div class="controls">
              <md-button class="md-raised md-primary" @click="toggleConnection">
                <md-icon>{{ isConnected ? "pause" : "play_arrow" }}</md-icon>
                {{ isConnected ? "暂停" : "开始" }}
              </md-button>
              <md-button class="md-raised" @click="clearData">
                <md-icon>clear</md-icon>
                清空数据
              </md-button>
            </div>
          </md-card-content>
        </md-card>
      </div>
    </div>
  </div>
</template>

<script>
import { Chart, registerables } from "chart.js";
import socketService from "@/plugins/socket";
import statsApi from "@/api/stats";

Chart.register(...registerables);

export default {
  name: "GpuMonitor",
  data() {
    return {
      chart: null,
      isConnected: false,
      latestMetric: null,
      maxDataPoints: 50, // 最多显示 50 个数据点
      chartData: {
        labels: [],
        datasets: [
          {
            label: "已使用 (MB)",
            data: [],
            borderColor: "rgb(255, 99, 132)",
            backgroundColor: "rgba(255, 99, 132, 0.1)",
            tension: 0.4,
            fill: true,
          },
          {
            label: "总容量 (MB)",
            data: [],
            borderColor: "rgb(54, 162, 235)",
            backgroundColor: "rgba(54, 162, 235, 0.1)",
            tension: 0.4,
            fill: true,
          },
        ],
      },
    };
  },
  mounted() {
    this.initChart();
    this.loadInitialData();
    this.connectWebSocket();
  },
  beforeDestroy() {
    this.disconnectWebSocket();
    if (this.chart) {
      this.chart.destroy();
    }
  },
  methods: {
    initChart() {
      const ctx = this.$refs.chartCanvas.getContext("2d");
      this.chart = new Chart(ctx, {
        type: "line",
        data: this.chartData,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: "显存 (MB)",
              },
            },
            x: {
              title: {
                display: true,
                text: "时间",
              },
            },
          },
          plugins: {
            legend: {
              display: true,
              position: "top",
            },
            tooltip: {
              mode: "index",
              intersect: false,
            },
          },
          interaction: {
            mode: "nearest",
            axis: "x",
            intersect: false,
          },
        },
      });
    },
    async loadInitialData() {
      try {
        const data = await statsApi.getGpuMetrics();
        if (data && data.metrics) {
          data.metrics.slice(-this.maxDataPoints).forEach((metric) => {
            this.addDataPoint(metric);
          });
        }
      } catch (error) {
        console.error("加载初始 GPU 数据失败:", error);
      }
    },
    connectWebSocket() {
      if (!socketService.isConnected()) {
        socketService.connect();
      }
      socketService.subscribe("gpu_metrics", this.handleGpuData);
      this.isConnected = true;
    },
    disconnectWebSocket() {
      socketService.unsubscribe("gpu_metrics");
      this.isConnected = false;
    },
    handleGpuData(data) {
      this.addDataPoint(data);
      this.latestMetric = data;
    },
    addDataPoint(metric) {
      const timestamp = new Date(metric.timestamp).toLocaleTimeString("zh-CN");

      this.chartData.labels.push(timestamp);
      this.chartData.datasets[0].data.push(metric.used);
      this.chartData.datasets[1].data.push(metric.total);

      // 限制数据点数量
      if (this.chartData.labels.length > this.maxDataPoints) {
        this.chartData.labels.shift();
        this.chartData.datasets[0].data.shift();
        this.chartData.datasets[1].data.shift();
      }

      this.chart.update("none"); // 'none' 模式性能更好
    },
    toggleConnection() {
      if (this.isConnected) {
        this.disconnectWebSocket();
      } else {
        this.connectWebSocket();
      }
    },
    clearData() {
      this.chartData.labels = [];
      this.chartData.datasets[0].data = [];
      this.chartData.datasets[1].data = [];
      this.latestMetric = null;
      this.chart.update();
    },
  },
};
</script>

<style scoped>
.status-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.chart-container {
  height: 400px;
  margin: 20px 0;
}

.controls {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 20px;
}
</style>

