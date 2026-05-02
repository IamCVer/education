<template>
  <div class="dialogue-panel">
    <div class="panel-header">
      <h2>多轮澄清与确认</h2>
      <div class="missing-list" v-if="missingFields.length">
        <span>仍待补充：</span>
        <el-tag v-for="field in missingFields" :key="field" size="mini" type="warning">
          {{ humanizeMissingField(field) }}
        </el-tag>
      </div>
    </div>

    <div class="message-list">
      <div v-if="!messages.length" class="empty-state">
        先在左侧输入教学需求，再点击“开始澄清需求”。
      </div>
      <div
        v-for="(message, index) in messages"
        :key="index"
        class="message-item"
        :class="message.role"
      >
        <div class="message-role">{{ message.role === 'assistant' ? '智能体' : '教师' }}</div>
        <div class="message-content">{{ message.content }}</div>
      </div>
    </div>

    <div class="summary-board" v-if="summaryText || assistantSuggestions.length">
      <div v-if="summaryText" class="summary-block">
        <span class="board-label">当前精简总结</span>
        <p>{{ summaryText }}</p>
      </div>
      <div v-if="assistantSuggestions.length" class="suggestion-block">
        <span class="board-label">AI 追问 / 优化建议</span>
        <div class="suggestion-list">
          <div v-for="(item, index) in assistantSuggestions" :key="index" class="suggestion-item">
            {{ item }}
          </div>
        </div>
      </div>
    </div>

    <div class="confirmation-card" v-if="confirmationCard && confirmationCard.summary">
      <div class="card-top">
        <div>
          <span class="card-label">教学意图确认卡</span>
          <h3>{{ confirmationCard.title }}</h3>
        </div>
        <el-tag size="small" :type="readyToGenerate ? 'success' : 'warning'">
          {{ readyToGenerate ? '信息完整' : '仍需补充' }}
        </el-tag>
      </div>
      <div class="summary-list">
        <div v-for="item in confirmationCard.summary" :key="item.label" class="summary-item">
          <div class="summary-label">{{ item.label }}</div>
          <div class="summary-value">{{ renderValue(item.value) }}</div>
        </div>
      </div>
    </div>

    <div class="followup-box">
      <div class="followup-head">
        <h3>继续补充 / 修改需求</h3>
        <div class="followup-tools">
          <el-button size="mini" :type="isListening ? 'danger' : 'default'" @click="toggleSpeech">
            {{ isListening ? '停止语音' : '语音输入' }}
          </el-button>
          <el-button size="mini" type="primary" @click="$emit('submit-followup')">提交本轮修改</el-button>
        </div>
      </div>
      <el-input
        :value="followupDraft"
        type="textarea"
        :rows="4"
        placeholder="例如：增加案例、补充互动环节、把难点讲解得更细"
        @input="$emit('update:followup-draft', $event)"
      />
      <div class="speech-status">{{ speechStatus }}</div>
    </div>
  </div>
</template>

<script>
import { humanizeMissingField } from '../utils/formatters'
import { mergeSpeechIntoDraft, startBrowserSpeechRecognition } from '../utils/speechRecognition'

export default {
  name: 'DialoguePanel',
  props: {
    messages: {
      type: Array,
      default: () => []
    },
    confirmationCard: {
      type: Object,
      default: () => ({})
    },
    missingFields: {
      type: Array,
      default: () => []
    },
    readyToGenerate: {
      type: Boolean,
      default: false
    },
    summaryText: {
      type: String,
      default: ''
    },
    assistantSuggestions: {
      type: Array,
      default: () => []
    },
    followupDraft: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      recognition: null,
      isListening: false,
      speechBaseDraft: '',
      speechStatus: '支持继续补充需求，每次提交都会刷新总结和确认卡'
    }
  },
  methods: {
    humanizeMissingField,
    renderValue(value) {
      return Array.isArray(value) ? value.join('；') : value
    },
    toggleSpeech() {
      if (this.isListening && this.recognition) {
        this.recognition.stop()
        return
      }
      try {
        this.recognition = startBrowserSpeechRecognition({
          onStart: () => {
            this.isListening = true
            this.speechBaseDraft = this.followupDraft || ''
            this.speechStatus = '正在识别中，请开始说话'
          },
          onResult: (transcript, payload = {}) => {
            this.$emit('update:followup-draft', mergeSpeechIntoDraft(this.speechBaseDraft, transcript))
            if (!payload.isFinal) {
              this.speechStatus = '正在识别，文本已实时写入本轮修改输入框'
              return
            }
            this.speechStatus = '识别成功，内容已写入本轮修改输入框'
          },
          onError: event => {
            this.speechStatus = `语音识别失败：${event.error || '请改用文字输入'}`
            this.$message.warning(this.speechStatus)
          },
          onEnd: () => {
            this.isListening = false
            this.speechBaseDraft = ''
          }
        })
      } catch (error) {
        this.speechStatus = error.message
        this.$message.warning(error.message)
      }
    }
  }
}
</script>

<style scoped>
.dialogue-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 100%;
}

.panel-header h2 {
  color: #16324f;
  font-size: 18px;
}

.missing-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  margin-top: 8px;
}

.message-list {
  flex: 1;
  min-height: 220px;
  max-height: 320px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.empty-state {
  border: 1px dashed #c7d2e0;
  border-radius: 18px;
  padding: 20px;
  color: #6b7280;
  background: #fbfdff;
}

.message-item {
  border-radius: 18px;
  padding: 14px;
}

.message-item.user {
  background: #eef6ff;
}

.message-item.assistant {
  background: #f8fafc;
}

.message-role {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 8px;
}

.message-content {
  color: #1f2937;
  white-space: pre-wrap;
  line-height: 1.6;
}

.confirmation-card {
  background: linear-gradient(145deg, #16324f, #205493);
  color: #fff;
  border-radius: 24px;
  padding: 18px;
}

.card-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.card-label {
  font-size: 12px;
  opacity: 0.8;
}

.card-top h3 {
  margin-top: 6px;
}

.summary-list {
  display: grid;
  gap: 10px;
}

.summary-item {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 10px 12px;
}

.summary-label {
  font-size: 12px;
  opacity: 0.78;
}

.summary-value {
  margin-top: 6px;
  line-height: 1.5;
}

.summary-board {
  display: grid;
  gap: 10px;
}

.summary-block,
.suggestion-block,
.followup-box {
  border-radius: 18px;
  border: 1px solid #d7e2ef;
  background: #f8fbff;
  padding: 14px;
}

.board-label {
  display: inline-block;
  margin-bottom: 8px;
  color: #2563eb;
  font-size: 12px;
}

.summary-block p {
  color: #334155;
  line-height: 1.6;
}

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-item {
  border-radius: 12px;
  background: white;
  padding: 10px 12px;
  color: #334155;
}

.followup-box {
  margin-top: auto;
}

.followup-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.followup-head h3 {
  color: #16324f;
  font-size: 16px;
}

.followup-tools {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.speech-status {
  margin-top: 8px;
  color: #64748b;
  font-size: 12px;
}
</style>
