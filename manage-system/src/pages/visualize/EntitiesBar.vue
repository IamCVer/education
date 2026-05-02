<template>
  <div class="content">
    <div class="md-layout">
      <!-- Degree Top 10 -->
      <div class="md-layout-item md-medium-size-100 md-size-50">
        <md-card>
          <md-card-header data-background-color="purple">
            <h4 class="title">连接数 (Degree) Top 10</h4>
            <p class="category">实体连接数排行</p>
          </md-card-header>
          <md-card-content>
            <div class="chart-container">
              <canvas ref="degreeChart"></canvas>
            </div>
            <md-button class="md-raised md-primary" @click="refreshData" style="margin-top: 20px">
              <md-icon>refresh</md-icon>
              刷新数据
            </md-button>
          </md-card-content>
        </md-card>
      </div>

      <!-- Frequency Top 10 -->
      <div class="md-layout-item md-medium-size-100 md-size-50">
        <md-card>
          <md-card-header data-background-color="green">
            <h4 class="title">频率 (Frequency) Top 10</h4>
            <p class="category">实体出现频率排行</p>
          </md-card-header>
          <md-card-content>
            <div class="chart-container">
              <canvas ref="frequencyChart"></canvas>
            </div>
            <md-button class="md-raised md-primary" @click="refreshData" style="margin-top: 20px">
              <md-icon>refresh</md-icon>
              刷新数据
            </md-button>
          </md-card-content>
        </md-card>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="md-layout">
      <div class="md-layout-item md-size-100">
        <md-card>
          <md-card-header data-background-color="blue">
            <h4 class="title">详细数据</h4>
          </md-card-header>
          <md-card-content>
            <md-tabs md-dynamic-height>
              <md-tab md-label="Degree Top 10">
                <md-table v-if="degreeData.length > 0">
                  <md-table-row>
                    <md-table-head>排名</md-table-head>
                    <md-table-head>实体名称</md-table-head>
                    <md-table-head>连接数</md-table-head>
                    <md-table-head>类型</md-table-head>
                  </md-table-row>
                  <md-table-row v-for="(item, index) in degreeData" :key="index">
                    <md-table-cell>{{ index + 1 }}</md-table-cell>
                    <md-table-cell>{{ item.entity }}</md-table-cell>
                    <md-table-cell>{{ item.degree }}</md-table-cell>
                    <md-table-cell>
                      <md-chip class="md-primary">{{ item.type || "N/A" }}</md-chip>
                    </md-table-cell>
                  </md-table-row>
                </md-table>
              </md-tab>
              <md-tab md-label="Frequency Top 10">
                <md-table v-if="frequencyData.length > 0">
                  <md-table-row>
                    <md-table-head>排名</md-table-head>
                    <md-table-head>实体名称</md-table-head>
                    <md-table-head>频率</md-table-head>
                    <md-table-head>类型</md-table-head>
                  </md-table-row>
                  <md-table-row v-for="(item, index) in frequencyData" :key="index">
                    <md-table-cell>{{ index + 1 }}</md-table-cell>
                    <md-table-cell>{{ item.entity }}</md-table-cell>
                    <md-table-cell>{{ item.frequency }}</md-table-cell>
                    <md-table-cell>
                      <md-chip class="md-accent">{{ item.type || "N/A" }}</md-chip>
                    </md-table-cell>
                  </md-table-row>
                </md-table>
              </md-tab>
            </md-tabs>
          </md-card-content>
        </md-card>
      </div>
    </div>
  </div>
</template>

<script>
import { Chart, registerables } from "chart.js";
import statsApi from "@/api/stats";

Chart.register(...registerables);

export default {
  name: "EntitiesBar",
  data() {
    return {
      degreeChart: null,
      frequencyChart: null,
      degreeData: [],
      frequencyData: [],
    };
  },
  mounted() {
    this.loadData();
  },
  beforeDestroy() {
    if (this.degreeChart) this.degreeChart.destroy();
    if (this.frequencyChart) this.frequencyChart.destroy();
  },
  methods: {
    async loadData() {
      try {
        const response = await statsApi.getEntitiesRanking();
        this.degreeData = response.degreeTop10 || [];
        this.frequencyData = response.frequencyTop10 || [];

        this.$nextTick(() => {
          this.renderDegreeChart();
          this.renderFrequencyChart();
        });
      } catch (error) {
        this.$notify({
          message: "加载实体排行数据失败: " + error,
          icon: "error",
          horizontalAlign: "right",
          verticalAlign: "top",
          type: "danger",
        });
      }
    },
    renderDegreeChart() {
      if (this.degreeChart) {
        this.degreeChart.destroy();
      }

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
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: "连接数",
              },
            },
            x: {
              ticks: {
                maxRotation: 45,
                minRotation: 45,
              },
            },
          },
          plugins: {
            legend: {
              display: false,
            },
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
      if (this.frequencyChart) {
        this.frequencyChart.destroy();
      }

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
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: "出现频率",
              },
            },
            x: {
              ticks: {
                maxRotation: 45,
                minRotation: 45,
              },
            },
          },
          plugins: {
            legend: {
              display: false,
            },
            tooltip: {
              callbacks: {
                label: (context) => `频率: ${context.parsed.y}`,
              },
            },
          },
        },
      });
    },
    refreshData() {
      this.loadData();
      this.$notify({
        message: "数据已刷新",
        icon: "check",
        horizontalAlign: "right",
        verticalAlign: "top",
        type: "success",
      });
    },
  },
};
</script>

<style scoped>
.chart-container {
  height: 350px;
  margin: 20px 0;
}
</style>

