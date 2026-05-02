<template>
  <div class="intent-panel">
    <div class="panel-head">
      <div>
        <h2>教师需求输入</h2>
        <p>把教学想法尽量说清楚，系统会自动追问补全。</p>
      </div>
      <el-tag size="mini" :type="readyToGenerate ? 'success' : 'warning'">
        {{ readyToGenerate ? '可生成' : '待补充' }}
      </el-tag>
    </div>

    <div class="intent-scroll">
      <div class="grid-form">
        <el-input :value="form.topic" placeholder="教学主题" @input="emitField('topic', $event)" />
        <el-input :value="form.subject" placeholder="学科" @input="emitField('subject', $event)" />
        <el-input :value="form.grade_level" placeholder="适用年级" @input="emitField('grade_level', $event)" />
        <el-input :value="form.lesson_duration" placeholder="课时/时长" @input="emitField('lesson_duration', $event)" />
      </div>

      <el-input
        :value="form.teaching_goals"
        type="textarea"
        :rows="2"
        placeholder="教学目标，一行一个"
        @input="emitField('teaching_goals', $event)"
      />

      <el-input
        :value="form.key_points"
        type="textarea"
        :rows="2"
        placeholder="核心知识点，一行一个"
        @input="emitField('key_points', $event)"
      />

      <el-input
        :value="form.difficult_points"
        type="textarea"
        :rows="1"
        placeholder="重点难点，一行一个"
        @input="emitField('difficult_points', $event)"
      />

      <el-input
        :value="form.style_requirements"
        type="textarea"
        :rows="1"
        placeholder="风格要求，例如：图文并茂、案例驱动、适合大二"
        @input="emitField('style_requirements', $event)"
      />

      <el-input
        :value="form.interaction_preferences"
        type="textarea"
        :rows="1"
        placeholder="互动设计要求，例如：随堂问答、小测验、翻转课堂"
        @input="emitField('interaction_preferences', $event)"
      />

      <el-input
        :value="messageDraft"
        type="textarea"
        :rows="4"
        placeholder="用自然语言补充你的整体教学思路、逻辑、案例要求和参考风格"
        @input="$emit('update-message', $event)"
      />

      <div class="speech-box">
        <el-button size="small" :type="isListening ? 'danger' : 'default'" @click="toggleSpeech">
          <i :class="isListening ? 'el-icon-microphone' : 'el-icon-headset'"></i>
          {{ isListening ? '停止语音输入' : '语音转文字' }}
        </el-button>
        <span class="speech-tip">{{ speechHint }}</span>
      </div>
    </div>

    <div class="actions">
      <el-button :loading="clarifying" type="primary" icon="el-icon-chat-line-round" @click="$emit('clarify')">
        {{ clarifying ? '分析中' : '开始澄清需求' }}
      </el-button>
      <el-button :loading="generating" type="success" icon="el-icon-magic-stick" @click="$emit('generate')">
        {{ generating ? '生成中' : '一键生成课件' }}
      </el-button>
    </div>
  </div>
</template>

<script>
import { mergeSpeechIntoDraft, startBrowserSpeechRecognition } from '../utils/speechRecognition'

export default {
  name: 'IntentPanel',
  props: {
    form: {
      type: Object,
      required: true
    },
    messageDraft: {
      type: String,
      default: ''
    },
    clarifying: {
      type: Boolean,
      default: false
    },
    generating: {
      type: Boolean,
      default: false
    },
    readyToGenerate: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      recognition: null,
      isListening: false,
      speechBaseDraft: '',
      speechHint: '优先调用浏览器内置语音识别，识别结果会自动写入下方文本框'
    }
  },
  methods: {
    emitField(field, value) {
      this.$emit('update-field', { field, value })
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
            this.speechBaseDraft = this.messageDraft || ''
            this.speechHint = '正在识别，请开始说话'
          },
          onResult: (transcript, payload = {}) => {
            this.$emit('update-message', mergeSpeechIntoDraft(this.speechBaseDraft, transcript))
            if (!payload.isFinal) {
              this.speechHint = '正在识别，文本已实时写入输入框'
              return
            }
            this.speechHint = '识别成功，结果已写入输入框'
          },
          onError: event => {
            this.speechHint = `语音识别失败：${event.error || '请改用文字输入'}`
            this.$message.warning(this.speechHint)
          },
          onEnd: () => {
            this.isListening = false
            this.speechBaseDraft = ''
          }
        })
      } catch (error) {
        this.speechHint = error.message
        this.$message.warning(error.message)
      }
    }
  }
}
</script>

<style scoped>
.intent-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 0;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.panel-head h2 {
  font-size: 18px;
  color: #16324f;
}

.panel-head p {
  margin-top: 6px;
  color: #5f6c7b;
  font-size: 13px;
  line-height: 1.5;
}

.grid-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.intent-scroll {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px;
}

.speech-box {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.speech-tip {
  color: #5f6c7b;
  font-size: 12px;
}

.actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  position: sticky;
  bottom: 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.72) 0%, rgba(255, 255, 255, 0.96) 28%, #fff 100%);
  padding-top: 10px;
  margin-top: auto;
}
</style>
