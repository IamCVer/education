<template>
  <div class="ppt-task-panel">
    <div class="task-head">
      <div>
        <h3>PPT 任务</h3>
        <p>真实调用讯飞 PPT 生成接口</p>
      </div>
      <el-tag size="small" :type="tagType">{{ statusText }}</el-tag>
    </div>

    <div class="task-body">
      <div class="row"><span>任务 ID</span><strong>{{ pptTask.sid || '未提交' }}</strong></div>
      <div class="row"><span>进度</span><strong>{{ pptTask.progress_text || '等待生成' }}</strong></div>
      <div class="row" v-if="pptTask.error_message"><span>错误</span><strong>{{ pptTask.error_message }}</strong></div>
    </div>

    <div class="task-actions">
      <el-button size="small" icon="el-icon-refresh" :disabled="!pptTask.sid" @click="$emit('refresh')">
        刷新状态
      </el-button>
      <el-button
        size="small"
        type="primary"
        icon="el-icon-download"
        :disabled="!pptTask.download_url"
        @click="$emit('download')"
      >
        下载 PPT
      </el-button>
    </div>
  </div>
</template>

<script>
import { formatPptStatus } from '../utils/formatters'

export default {
  name: 'PptTaskPanel',
  props: {
    pptTask: {
      type: Object,
      default: () => ({})
    }
  },
  computed: {
    statusText() {
      return formatPptStatus(this.pptTask.status)
    },
    tagType() {
      if (['done', 'finished'].includes(this.pptTask.status)) return 'success'
      if (this.pptTask.status === 'fail') return 'danger'
      if (this.pptTask.status === 'building') return 'warning'
      return 'info'
    }
  }
}
</script>

<style scoped>
.ppt-task-panel {
  border-radius: 18px;
  border: 1px solid #d7e2ef;
  background: #f8fbff;
  padding: 16px;
}

.task-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.task-head h3 {
  color: #16324f;
}

.task-head p {
  margin-top: 6px;
  color: #64748b;
  font-size: 12px;
}

.task-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 14px;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #334155;
}

.task-actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
  flex-wrap: wrap;
}
</style>
