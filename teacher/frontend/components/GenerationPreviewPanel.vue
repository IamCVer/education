<template>
  <div class="generation-panel">
    <PptTaskPanel :ppt-task="pptTask" @refresh="$emit('refresh-ppt')" @download="$emit('download-ppt')" />

    <div class="block">
      <div class="block-head">
        <h3>Word 教案预览</h3>
        <el-button size="small" icon="el-icon-download" @click="$emit('download-lesson-plan')">下载 DOCX</el-button>
      </div>
      <div v-if="lessonPlanPreview" class="lesson-plan" v-html="lessonPlanPreview"></div>
      <div v-else class="empty">生成后会在这里展示教案预览。</div>
    </div>

    <div class="block">
      <div class="block-head">
        <h3>互动内容预览</h3>
        <el-button size="small" icon="el-icon-download" @click="$emit('download-interactive')">下载 HTML</el-button>
      </div>
      <iframe v-if="interactiveHtml" class="interactive-frame" :srcdoc="interactiveHtml"></iframe>
      <div v-else class="empty">生成后会在这里展示互动内容。</div>
    </div>

    <div class="block meta-block">
      <div class="meta-col">
        <h3>参考资料摘要</h3>
        <div v-if="references.length" class="meta-list">
          <div v-for="item in references" :key="item.file_id" class="meta-item">
            <strong>{{ item.file_name }}</strong>
            <p>{{ item.summary }}</p>
          </div>
        </div>
        <div v-else class="empty mini">还没有上传资料。</div>
      </div>
      <div class="meta-col">
        <h3>知识库检索片段</h3>
        <div v-if="retrievals.length" class="meta-list">
          <div v-for="(item, index) in retrievals" :key="index" class="meta-item">
            <div class="meta-title-row">
              <strong>{{ item.title || item.source }}</strong>
              <el-tag size="mini">{{ item.source }}</el-tag>
            </div>
            <p>{{ item.description || item.text }}</p>
          </div>
        </div>
        <div v-else class="empty mini">生成后会展示检索片段。</div>
      </div>
    </div>

    <div class="block">
      <div class="block-head">
        <h3>修改意见与再生成</h3>
        <el-button size="small" type="primary" :loading="generating" @click="$emit('revise')">
          {{ generating ? '处理中' : '根据意见再生成' }}
        </el-button>
      </div>
      <el-input
        :value="revisionNote"
        type="textarea"
        :rows="4"
        placeholder="例如：增加一个案例、简化第三部分、把互动环节改成选择题"
        @input="$emit('update:revision-note', $event)"
      />
    </div>
  </div>
</template>

<script>
import PptTaskPanel from './PptTaskPanel.vue'

export default {
  name: 'GenerationPreviewPanel',
  components: {
    PptTaskPanel
  },
  props: {
    pptTask: {
      type: Object,
      default: () => ({})
    },
    lessonPlanPreview: {
      type: String,
      default: ''
    },
    interactiveHtml: {
      type: String,
      default: ''
    },
    references: {
      type: Array,
      default: () => []
    },
    retrievals: {
      type: Array,
      default: () => []
    },
    revisionNote: {
      type: String,
      default: ''
    },
    generating: {
      type: Boolean,
      default: false
    }
  }
}
</script>

<style scoped>
.generation-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.block {
  border-radius: 18px;
  border: 1px solid #d7e2ef;
  background: #fff;
  padding: 16px;
}

.block-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.block-head h3 {
  color: #16324f;
}

.lesson-plan {
  max-height: 280px;
  overflow-y: auto;
  line-height: 1.6;
}

.interactive-frame {
  width: 100%;
  height: 300px;
  border: none;
  border-radius: 14px;
  background: #f8fafc;
}

.meta-block {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.meta-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.meta-item {
  background: #f8fbff;
  border-radius: 12px;
  padding: 10px;
}

.meta-item p {
  margin-top: 6px;
  color: #475569;
  line-height: 1.5;
  font-size: 13px;
}

.meta-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.empty {
  border: 1px dashed #c7d2e0;
  border-radius: 14px;
  padding: 18px;
  color: #6b7280;
}

.empty.mini {
  padding: 12px;
}

@media (max-width: 1100px) {
  .meta-block {
    grid-template-columns: 1fr;
  }
}
</style>
