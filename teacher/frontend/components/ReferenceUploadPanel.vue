<template>
  <div class="reference-panel">
    <div class="header">
      <h3>参考资料上传</h3>
      <span>支持 PDF / DOCX / PPTX / 图片 / 视频</span>
    </div>

    <el-input
      v-model="purpose"
      type="textarea"
      :rows="2"
      placeholder="说明这些资料的用途，例如：参考此 PDF 的知识点结构，参考视频中的课堂案例"
    />

    <div class="toolbar">
      <input
        ref="fileInput"
        class="native-input"
        type="file"
        multiple
        accept=".pdf,.docx,.pptx,.txt,.md,image/*,video/*"
        @change="handleFileChange"
      >
      <el-button size="small" icon="el-icon-folder-opened" @click="$refs.fileInput.click()">选择文件</el-button>
      <el-button
        size="small"
        type="primary"
        :loading="uploading"
        :disabled="!selectedFiles.length"
        @click="submitUpload"
      >
        {{ uploading ? '上传中' : '上传并解析' }}
      </el-button>
    </div>

    <div v-if="selectedFiles.length" class="selected-files">
      <div v-for="file in selectedFiles" :key="file.name + file.size" class="selected-item">
        <i class="el-icon-paperclip"></i>
        <span>{{ file.name }}</span>
      </div>
    </div>

    <div class="reference-list">
      <div v-for="item in references" :key="item.file_id" class="reference-item">
        <div class="reference-meta">
          <strong>{{ item.file_name }}</strong>
          <el-tag size="mini">{{ item.file_type }}</el-tag>
        </div>
        <div class="reference-purpose" v-if="item.purpose">用途：{{ item.purpose }}</div>
        <div class="reference-summary">{{ item.summary }}</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ReferenceUploadPanel',
  props: {
    references: {
      type: Array,
      default: () => []
    },
    uploading: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      selectedFiles: [],
      purpose: ''
    }
  },
  methods: {
    handleFileChange(event) {
      this.selectedFiles = Array.from(event.target.files || [])
    },
    submitUpload() {
      if (!this.selectedFiles.length) {
        this.$message.warning('请先选择资料文件')
        return
      }
      this.$emit('upload-selected', {
        files: this.selectedFiles,
        purpose: this.purpose
      })
      this.selectedFiles = []
      this.purpose = ''
      this.$refs.fileInput.value = ''
    }
  }
}
</script>

<style scoped>
.reference-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

.header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.header h3 {
  color: #16324f;
  font-size: 16px;
}

.header span {
  color: #6b7280;
  font-size: 12px;
}

.toolbar {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.native-input {
  display: none;
}

.selected-files,
.reference-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reference-list {
  max-height: 180px;
  overflow-y: auto;
  padding-right: 4px;
}

.selected-item,
.reference-item {
  border-radius: 14px;
  background: #f8fbff;
  border: 1px solid #d8e5f4;
  padding: 10px 12px;
}

.reference-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 6px;
}

.reference-purpose {
  font-size: 12px;
  color: #2563eb;
  margin-bottom: 6px;
}

.reference-summary {
  color: #4b5563;
  line-height: 1.5;
  font-size: 13px;
}
</style>
