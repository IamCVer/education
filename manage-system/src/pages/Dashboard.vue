<template>
  <div class="content">
    <div class="md-layout">
      <!-- GPU 显存监控 -->
      <div class="md-layout-item md-medium-size-100 md-xsmall-size-100 md-size-100">
        <md-card>
          <md-card-header data-background-color="orange">
            <h4 class="title">{{ monitorType === 'gpu' ? 'GPU 显存监控' : 'CPU/内存监控' }}</h4>
            <p class="category">
              <md-chip :class="isGpuConnected ? 'md-primary' : 'md-accent'" style="margin: 0">
                <md-icon>{{ isGpuConnected ? "wifi" : "wifi_off" }}</md-icon>
                {{ isGpuConnected ? "实时连接" : "已断开" }}
              </md-chip>
              <md-chip v-if="latestGpuMetric" class="md-primary" style="margin-left: 10px">
                <span v-if="monitorType === 'gpu'">
                  GPU: {{ latestGpuMetric.used }} MB / {{ latestGpuMetric.total }} MB ({{ latestGpuMetric.percentage }}%)
                </span>
                <span v-else>
                  CPU: {{ latestGpuMetric.percentage }}% | 内存: {{ latestGpuMetric.memory_percent }}%
                </span>
              </md-chip>
            </p>
          </md-card-header>
          <md-card-content>
            <div class="chart-container" style="height: 300px">
              <canvas ref="gpuChart"></canvas>
            </div>
            <div style="text-align: center; margin-top: 10px">
              <md-button class="md-raised md-primary md-sm" @click="toggleGpuConnection">
                <md-icon>{{ isGpuConnected ? "pause" : "play_arrow" }}</md-icon>
                {{ isGpuConnected ? "暂停" : "开始" }}
              </md-button>
              <md-button class="md-raised md-sm" @click="clearGpuData">
                <md-icon>clear</md-icon>
                清空
              </md-button>
            </div>
          </md-card-content>
        </md-card>
      </div>
      <!-- 实体排行 - Degree Top 10 -->
      <div class="md-layout-item md-medium-size-100 md-size-50">
        <md-card>
          <md-card-header data-background-color="purple">
            <h4 class="title">连接数 (Degree) Top 10</h4>
            <p class="category">实体连接数排行</p>
          </md-card-header>
          <md-card-content>
            <div class="chart-container" style="height: 350px">
              <canvas ref="degreeChart"></canvas>
            </div>
          </md-card-content>
        </md-card>
      </div>

      <!-- 实体排行 - Frequency Top 10 -->
      <div class="md-layout-item md-medium-size-100 md-size-50">
        <md-card>
          <md-card-header data-background-color="green">
            <h4 class="title">频率 (Frequency) Top 10</h4>
            <p class="category">实体出现频率排行</p>
          </md-card-header>
          <md-card-content>
            <div class="chart-container" style="height: 350px">
              <canvas ref="frequencyChart"></canvas>
            </div>
          </md-card-content>
        </md-card>
      </div>
      <!-- 知识图谱力导向图 -->
      <div class="md-layout-item md-medium-size-100 md-xsmall-size-100 md-size-100">
        <md-card>
          <md-card-header data-background-color="red">
            <h4 class="title">知识图谱网络关系图</h4>
            <p class="category">实体关系力导向可视化 - 展示知识节点的网络连接</p>
          </md-card-header>
          <md-card-content>
            <div v-if="loadingForceGraph" style="text-align: center; padding: 40px">
              <md-progress-spinner md-mode="indeterminate"></md-progress-spinner>
              <p>加载中...</p>
            </div>
            <div v-else ref="forceGraphChart" class="chart-container" style="height: 600px"></div>
            <div style="text-align: center; margin-top: 10px">
              <md-button class="md-raised md-primary md-sm" @click="loadAllData">
                <md-icon>refresh</md-icon>
                刷新所有数据
              </md-button>
            </div>
            <!-- 统计信息 -->
            <div v-if="forceGraphStats" class="stats-panel" style="margin-top: 20px">
              <div class="stats-grid">
                <div class="stat-item">
                  <md-icon>hub</md-icon>
                  <div>
                    <div class="stat-label">节点数</div>
                    <div class="stat-value">{{ forceGraphStats.totalNodes }}</div>
                  </div>
                </div>
                <div class="stat-item">
                  <md-icon>share</md-icon>
                  <div>
                    <div class="stat-label">关系数</div>
                    <div class="stat-value">{{ forceGraphStats.totalLinks }}</div>
                  </div>
                </div>
                <div class="stat-item">
                  <md-icon>account_tree</md-icon>
                  <div>
                    <div class="stat-label">社区数</div>
                    <div class="stat-value">{{ forceGraphStats.communities }}</div>
                  </div>
                </div>
              </div>
            </div>
            <!-- 图例说明 -->
            <div style="margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 8px;">
              <p style="margin: 0; color: #666; font-size: 13px;">
                <strong>📊 图例说明：</strong><br>
                • <strong>节点大小</strong>：表示该实体的连接度（degree），节点越大表示与其他实体的关联越多<br>
                • <strong>节点颜色</strong>：不同颜色代表不同的社区（紧密联系的节点群）<br>
                • <strong>边/连线</strong>：表示实体之间的关系，鼠标悬停可查看详情<br>
                • <strong>拖拽交互</strong>：可以拖动节点查看不同角度的网络结构
              </p>
            </div>
          </md-card-content>
        </md-card>
      </div>
    </div>
  </div>
</template>

<script>
import { Chart, registerables } from "chart.js";
import * as echarts from "echarts";
import socketService from "@/plugins/socket";
import statsApi from "@/api/stats";

Chart.register(...registerables);

export default {
  name: "Dashboard",
  data() {
    return {
      // GPU/CPU 监控
      gpuChart: null,
      isGpuConnected: false,
      latestGpuMetric: null,
      maxGpuDataPoints: 30,
      monitorType: 'cpu', // 'gpu' 或 'cpu'
      gpuChartData: {
        labels: [],
        datasets: [
          {
            label: "已使用",
            data: [],
            borderColor: "rgb(255, 99, 132)",
            backgroundColor: "rgba(255, 99, 132, 0.1)",
            tension: 0.4,
            fill: true,
          },
          {
            label: "总容量",
            data: [],
            borderColor: "rgb(54, 162, 235)",
            backgroundColor: "rgba(54, 162, 235, 0.1)",
            tension: 0.4,
            fill: true,
          },
        ],
      },
      // 实体排行
      degreeChart: null,
      frequencyChart: null,
      degreeData: [],
      frequencyData: [],
      // 力导向图
      forceGraphChart: null,
      loadingForceGraph: false,
      forceGraphData: null,
      forceGraphStats: null,
    };
  },
  mounted() {
    this.initCharts();
    this.loadAllData();
    this.connectGpuWebSocket();
  },
  beforeDestroy() {
    this.disconnectGpuWebSocket();
    if (this.gpuChart) this.gpuChart.destroy();
    if (this.degreeChart) this.degreeChart.destroy();
    if (this.frequencyChart) this.frequencyChart.destroy();
    if (this.forceGraphChart) this.forceGraphChart.dispose();
  },
  methods: {
    // ============ 初始化图表 ============
    initCharts() {
      this.$nextTick(() => {
        this.initGpuChart();
        this.initEntityCharts();
      });
    },
    initGpuChart() {
      if (!this.$refs.gpuChart) return;
      const ctx = this.$refs.gpuChart.getContext("2d");
      this.gpuChart = new Chart(ctx, {
        type: "line",
        data: this.gpuChartData,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              title: { display: true, text: this.monitorType === 'gpu' ? "显存 (MB)" : "使用率 (%)" },
            },
            x: {
              title: { display: true, text: "时间" },
            },
          },
          plugins: {
            legend: { display: true, position: "top" },
            tooltip: { mode: "index", intersect: false },
          },
        },
      });
    },
    initEntityCharts() {
      // 初始化为空，等待数据加载
    },
    // ============ GPU 监控 ============
    async loadGpuInitialData() {
      try {
        const data = await statsApi.getGpuMetrics();
        if (data && data.metrics && data.metrics.length > 0) {
          // 检测监控类型
          const firstMetric = data.metrics[0];
          this.monitorType = firstMetric.type || 'cpu';
          
          // 更新图表标签
          if (this.monitorType === 'cpu') {
            this.gpuChartData.datasets[0].label = "CPU 使用率 (%)";
            this.gpuChartData.datasets[1].label = "内存使用率 (%)";
          }
          
          data.metrics.slice(-this.maxGpuDataPoints).forEach((metric) => {
            this.addGpuDataPoint(metric);
          });
        }
      } catch (error) {
        console.error("加载初始系统数据失败:", error);
        // 使用模拟数据
        this.useMockData();
      }
    },
    connectGpuWebSocket() {
      if (!socketService.isConnected()) {
        socketService.connect();
      }
      socketService.subscribe("gpu_metrics", this.handleGpuData);
      this.isGpuConnected = true;
    },
    disconnectGpuWebSocket() {
      socketService.unsubscribe("gpu_metrics");
      this.isGpuConnected = false;
    },
    handleGpuData(data) {
      this.addGpuDataPoint(data);
      this.latestGpuMetric = data;
    },
    addGpuDataPoint(metric) {
      const timestamp = new Date(metric.timestamp).toLocaleTimeString("zh-CN");
      this.gpuChartData.labels.push(timestamp);
      
      if (metric.type === 'cpu') {
        // CPU 模式：显示 CPU 使用率和内存使用率（百分比）
        this.gpuChartData.datasets[0].data.push(metric.percentage);
        this.gpuChartData.datasets[1].data.push(metric.memory_percent);
      } else {
        // GPU 模式：显示显存使用量
        this.gpuChartData.datasets[0].data.push(metric.used);
        this.gpuChartData.datasets[1].data.push(metric.total);
      }

      if (this.gpuChartData.labels.length > this.maxGpuDataPoints) {
        this.gpuChartData.labels.shift();
        this.gpuChartData.datasets[0].data.shift();
        this.gpuChartData.datasets[1].data.shift();
      }
      if (this.gpuChart) {
        this.gpuChart.update("none");
      }
    },
    useMockData() {
      // 使用模拟数据
      this.monitorType = 'cpu';
      this.gpuChartData.datasets[0].label = "CPU 使用率 (%)";
      this.gpuChartData.datasets[1].label = "内存使用率 (%)";
      
      for (let i = 0; i < 10; i++) {
        const now = new Date();
        now.setSeconds(now.getSeconds() - (10 - i) * 5);
        this.addGpuDataPoint({
          timestamp: now.toISOString(),
          type: 'cpu',
          percentage: Math.random() * 30 + 40,
          memory_percent: Math.random() * 20 + 50,
          used: 0,
          total: 0
        });
      }
    },
    toggleGpuConnection() {
      if (this.isGpuConnected) {
        this.disconnectGpuWebSocket();
      } else {
        this.connectGpuWebSocket();
      }
    },
    clearGpuData() {
      this.gpuChartData.labels = [];
      this.gpuChartData.datasets[0].data = [];
      this.gpuChartData.datasets[1].data = [];
      this.latestGpuMetric = null;
      if (this.gpuChart) {
        this.gpuChart.update();
      }
    },
    // ============ 实体排行 ============
    async loadEntityRanking() {
      try {
        const response = await statsApi.getEntitiesRanking();
        this.degreeData = response.degreeTop10 || [];
        this.frequencyData = response.frequencyTop10 || [];
        this.$nextTick(() => {
          this.renderDegreeChart();
          this.renderFrequencyChart();
        });
      } catch (error) {
        console.error("加载实体排行数据失败:", error);
      }
    },
    renderDegreeChart() {
      if (this.degreeChart) this.degreeChart.destroy();
      if (!this.$refs.degreeChart) return;

      const ctx = this.$refs.degreeChart.getContext("2d");
      const labels = this.degreeData.map((item) => item.entity);
      const data = this.degreeData.map((item) => item.degree);

      this.degreeChart = new Chart(ctx, {
        type: "bar",
        data: {
          labels: labels,
          datasets: [
            {
              label: "连接数",
              data: data,
              backgroundColor: "rgba(156, 39, 176, 0.6)",
              borderColor: "rgba(156, 39, 176, 1)",
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { beginAtZero: true, title: { display: true, text: "连接数" } },
            x: { ticks: { maxRotation: 45, minRotation: 45 } },
          },
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (context) => `连接数: ${context.parsed.y}`,
              },
            },
          },
        },
      });
    },
    renderFrequencyChart() {
      if (this.frequencyChart) this.frequencyChart.destroy();
      if (!this.$refs.frequencyChart) return;

      const ctx = this.$refs.frequencyChart.getContext("2d");
      const labels = this.frequencyData.map((item) => item.entity);
      const data = this.frequencyData.map((item) => item.frequency);

      this.frequencyChart = new Chart(ctx, {
        type: "bar",
        data: {
          labels: labels,
          datasets: [
            {
              label: "频率",
              data: data,
              backgroundColor: "rgba(76, 175, 80, 0.6)",
              borderColor: "rgba(76, 175, 80, 1)",
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { beginAtZero: true, title: { display: true, text: "出现频率" } },
            x: { ticks: { maxRotation: 45, minRotation: 45 } },
          },
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (context) => `频率: ${context.parsed.y}`,
              },
            },
          },
        },
      });
    },
    // ============ 力导向图 ============
    async loadForceGraph() {
      this.loadingForceGraph = true;
      try {
        const response = await statsApi.getForceGraph();
        console.log("力导向图数据:", response);
        console.log("节点数:", response.nodes?.length, "边数:", response.links?.length);
        
        this.forceGraphData = response;
        this.forceGraphStats = response.stats;
        
        this.$nextTick(() => {
          console.log("开始渲染力导向图...");
          this.renderForceGraph();
        });
      } catch (error) {
        console.error("加载力导向图数据失败:", error);
        this.$notify({
          message: "加载图表数据失败: " + error,
          icon: "error",
          horizontalAlign: "right",
          verticalAlign: "top",
          type: "danger",
        });
      } finally {
        this.loadingForceGraph = false;
      }
    },
    renderForceGraph() {
      console.log("renderForceGraph 被调用");
      console.log("forceGraphData:", this.forceGraphData);
      console.log("forceGraphChart ref:", this.$refs.forceGraphChart);
      
      if (!this.forceGraphData) {
        console.error("没有力导向图数据");
        return;
      }
      
      if (!this.$refs.forceGraphChart) {
        console.error("图表容器未找到");
        return;
      }

      if (this.forceGraphChart) {
        this.forceGraphChart.dispose();
      }

      console.log("初始化 ECharts...");
      this.forceGraphChart = echarts.init(this.$refs.forceGraphChart);

      // 确保每个节点都有 category 字段（作为数字索引）
      const nodes = this.forceGraphData.nodes.map(node => ({
        ...node,
        category: parseInt(node.category) || 0  // 确保是数字
      }));

      const option = {
        tooltip: {
          trigger: 'item',
          formatter: (params) => {
            if (params.dataType === 'node') {
              return `<strong>${params.data.name}</strong><br/>
                      类型: ${params.data.type || '未知'}<br/>
                      连接度: ${params.data.value || 0}`;
            } else if (params.dataType === 'edge') {
              return `关系: ${params.data.source} → ${params.data.target}`;
            }
          }
        },
        series: [{
          type: 'graph',
          layout: 'force',
          data: nodes,
          links: this.forceGraphData.links,
          roam: true,
          draggable: true,
          focusNodeAdjacency: true,
          label: {
            show: true,
            position: 'right',
            formatter: '{b}',
            fontSize: 9
          },
          lineStyle: {
            color: '#999',
            width: 1,
            curveness: 0.2,
            opacity: 0.5
          },
          emphasis: {
            focus: 'adjacency',
            label: {
              show: true,
              fontSize: 12
            },
            lineStyle: {
              width: 2,
              opacity: 0.8
            }
          },
          force: {
            initLayout: 'circular',
            repulsion: 400,
            gravity: 0.05,
            edgeLength: 100,
            layoutAnimation: true,
            friction: 0.6
          }
        }]
      };

      console.log("设置 ECharts 配置...");
      console.log("option:", option);
      console.log("nodes count:", option.series[0].data.length);
      console.log("links count:", option.series[0].links.length);
      console.log("sample node:", option.series[0].data[0]);
      console.log("sample link:", option.series[0].links[0]);
      
      // 保存到 window 以便调试
      window.lastForceGraphOption = option;
      window.lastForceGraphChart = this.forceGraphChart;
      
      // 使用 notMerge 强制重新渲染
      this.forceGraphChart.setOption(option, true);
      
      console.log("✓ 力导向图渲染完成");
      console.log("图表实例:", this.forceGraphChart);
      
      window.addEventListener("resize", this.handleResize);
    },
    handleResize() {
      if (this.forceGraphChart) {
        this.forceGraphChart.resize();
      }
    },
    // ============ 统一加载 ============
    async loadAllData() {
      await this.loadGpuInitialData();
      await this.loadEntityRanking();
      await this.loadForceGraph();
    },
  },
};
</script>

<style scoped>
.chart-container {
  position: relative;
}

.stats-panel {
  margin-top: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background-color: #f5f5f5;
  border-radius: 8px;
}

.stat-item .md-icon {
  font-size: 36px;
  color: #9c27b0;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}
</style>
