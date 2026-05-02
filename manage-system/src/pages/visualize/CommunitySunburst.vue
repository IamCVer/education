<template>
  <div class="content">
    <div class="md-layout">
      <div class="md-layout-item md-medium-size-100 md-xsmall-size-100 md-size-100">
        <md-card>
          <md-card-header data-background-color="red">
            <h4 class="title">社区层级旭日图</h4>
            <p class="category">知识图谱社区结构可视化</p>
          </md-card-header>
          <md-card-content>
            <!-- 加载状态 -->
            <div v-if="loading" style="text-align: center; padding: 40px">
              <md-progress-spinner md-mode="indeterminate"></md-progress-spinner>
              <p>加载中...</p>
            </div>

            <!-- 图表容器 -->
            <div v-else ref="chartContainer" class="chart-container"></div>

            <!-- 控制面板 -->
            <div class="controls">
              <md-button class="md-raised md-primary" @click="loadData">
                <md-icon>refresh</md-icon>
                刷新数据
              </md-button>
              <md-button class="md-raised" @click="resetZoom">
                <md-icon>zoom_out_map</md-icon>
                重置缩放
              </md-button>
            </div>

            <!-- 统计信息 -->
            <div v-if="stats" class="stats-panel">
              <md-card>
                <md-card-content>
                  <h4>统计信息</h4>
                  <div class="stats-grid">
                    <div class="stat-item">
                      <md-icon>account_tree</md-icon>
                      <div>
                        <div class="stat-label">总社区数</div>
                        <div class="stat-value">{{ stats.totalCommunities }}</div>
                      </div>
                    </div>
                    <div class="stat-item">
                      <md-icon>layers</md-icon>
                      <div>
                        <div class="stat-label">最大层级</div>
                        <div class="stat-value">{{ stats.maxLevel }}</div>
                      </div>
                    </div>
                    <div class="stat-item">
                      <md-icon>hub</md-icon>
                      <div>
                        <div class="stat-label">总实体数</div>
                        <div class="stat-value">{{ stats.totalEntities }}</div>
                      </div>
                    </div>
                  </div>
                </md-card-content>
              </md-card>
            </div>
          </md-card-content>
        </md-card>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from "echarts";
import statsApi from "@/api/stats";

export default {
  name: "CommunitySunburst",
  data() {
    return {
      chart: null,
      loading: false,
      treeData: null,
      stats: null,
    };
  },
  mounted() {
    this.loadData();
  },
  beforeDestroy() {
    if (this.chart) {
      this.chart.dispose();
    }
  },
  methods: {
    async loadData() {
      this.loading = true;
      try {
        const response = await statsApi.getCommunityTree();
        this.treeData = response.tree;
        this.stats = response.stats;

        this.$nextTick(() => {
          this.renderChart();
        });
      } catch (error) {
        this.$notify({
          message: "加载社区数据失败: " + error,
          icon: "error",
          horizontalAlign: "right",
          verticalAlign: "top",
          type: "danger",
        });
      } finally {
        this.loading = false;
      }
    },
    renderChart() {
      if (!this.treeData) return;

      if (this.chart) {
        this.chart.dispose();
      }

      this.chart = echarts.init(this.$refs.chartContainer);

      const option = {
        tooltip: {
          trigger: "item",
          formatter: (params) => {
            const { name, value, data } = params;
            let html = `<strong>${name}</strong><br/>`;
            html += `大小: ${value}<br/>`;
            if (data.level !== undefined) {
              html += `层级: ${data.level}<br/>`;
            }
            if (data.type) {
              html += `类型: ${data.type}<br/>`;
            }
            return html;
          },
        },
        series: [
          {
            type: "sunburst",
            data: [this.treeData],
            radius: [0, "90%"],
            label: {
              rotate: "radial",
              fontSize: 11,
            },
            itemStyle: {
              borderRadius: 7,
              borderWidth: 2,
              borderColor: "#fff",
            },
            levels: [
              {},
              {
                r0: "0%",
                r: "30%",
                label: {
                  rotate: 0,
                  fontSize: 14,
                  fontWeight: "bold",
                },
                itemStyle: {
                  borderWidth: 3,
                },
              },
              {
                r0: "30%",
                r: "55%",
                label: {
                  fontSize: 12,
                },
              },
              {
                r0: "55%",
                r: "75%",
                label: {
                  fontSize: 10,
                },
              },
              {
                r0: "75%",
                r: "90%",
                label: {
                  position: "outside",
                  padding: 3,
                  silent: false,
                  fontSize: 9,
                },
                itemStyle: {
                  borderWidth: 1,
                },
              },
            ],
            emphasis: {
              focus: "ancestor",
            },
          },
        ],
      };

      this.chart.setOption(option);

      // 响应式调整
      window.addEventListener("resize", this.handleResize);
    },
    handleResize() {
      if (this.chart) {
        this.chart.resize();
      }
    },
    resetZoom() {
      if (this.chart) {
        this.chart.dispatchAction({
          type: "sunburstRootToNode",
          targetNodeId: this.treeData.name,
        });
      }
    },
  },
};
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 600px;
  margin: 20px 0;
}

.controls {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin: 20px 0;
}

.stats-panel {
  margin-top: 30px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-top: 16px;
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

