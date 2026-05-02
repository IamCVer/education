<template>
  <div class="teacher-agent-page">
    <div class="hero">
      <div>
        <span class="hero-tag">Teacher Workspace</span>
        <h1>多模态 AI 互动式教学智能体</h1>
        <p>需求澄清、资料解析、本地知识库、PPT、教案和互动内容都集中在这一页完成。</p>
      </div>
      <div class="hero-actions">
        <el-button size="small" icon="el-icon-back" @click="$router.push('/chat')">返回问答</el-button>
        <el-button size="small" type="primary" icon="el-icon-refresh" @click="resetWorkspace">重置工作台</el-button>
      </div>
    </div>

    <div class="workspace-grid">
      <section class="workspace-card left-card">
        <ReferenceUploadPanel
          :references="references"
          :uploading="uploading"
          @upload-selected="handleUpload"
        />
        <IntentPanel
          :form="intentForm"
          :message-draft="messageDraft"
          :clarifying="clarifying"
          :generating="generating"
          :ready-to-generate="readyToGenerate"
          @update-field="handleFieldUpdate"
          @update-message="messageDraft = $event"
          @append-message="appendMessageDraft"
          @clarify="handleClarify"
          @generate="handleGenerate"
        />
      </section>

      <section class="workspace-card middle-card">
        <DialoguePanel
          :messages="messages"
          :confirmation-card="confirmationCard"
          :missing-fields="missingFields"
          :ready-to-generate="readyToGenerate"
          :summary-text="summaryText"
          :assistant-suggestions="assistantSuggestions"
          :followup-draft="followupDraft"
          @update:followup-draft="followupDraft = $event"
          @append-followup="appendFollowupDraft"
          @submit-followup="submitFollowupClarify"
        />
      </section>

      <section class="workspace-card right-card">
        <GenerationPreviewPanel
          :ppt-task="pptTask"
          :lesson-plan-preview="lessonPlanPreview"
          :interactive-html="interactiveHtml"
          :references="references"
          :retrievals="retrievals"
          :revision-note="revisionNote"
          :generating="generating"
          @update:revision-note="revisionNote = $event"
          @revise="handleRevise"
          @refresh-ppt="refreshPptStatus"
          @download-ppt="downloadPpt"
          @download-lesson-plan="downloadLessonPlan"
          @download-interactive="downloadInteractive"
        />
      </section>
    </div>
  </div>
</template>

<script>
import DialoguePanel from './components/DialoguePanel.vue'
import GenerationPreviewPanel from './components/GenerationPreviewPanel.vue'
import IntentPanel from './components/IntentPanel.vue'
import ReferenceUploadPanel from './components/ReferenceUploadPanel.vue'
import {
  clarifyTeacherIntent,
  createTeacherSession,
  fetchTeacherSession,
  downloadTeacherInteractive,
  downloadTeacherLessonPlan,
  fetchTeacherPptStatus,
  generateTeacherAssets,
  reviseTeacherAssets,
  uploadTeacherReference
} from './api/teacherAgent'
import { arrayToLines } from './utils/formatters'

export default {
  name: 'TeacherAgentPage',
  components: {
    IntentPanel,
    ReferenceUploadPanel,
    DialoguePanel,
    GenerationPreviewPanel
  },
  data() {
    return {
      sessionId: '',
      clarifying: false,
      uploading: false,
      generating: false,
      pollingTimer: null,
      sessionPromise: null,
      messageDraft: '',
      followupDraft: '',
      revisionNote: '',
      readyToGenerate: false,
      missingFields: [],
      messages: [],
      references: [],
      retrievals: [],
      summaryText: '',
      assistantSuggestions: [],
      confirmationCard: {},
      lessonPlanPreview: '',
      interactiveHtml: '',
      pptTask: {},
      intentForm: {
        topic: '',
        subject: '',
        grade_level: '',
        lesson_duration: '',
        teaching_goals: '',
        key_points: '',
        difficult_points: '',
        style_requirements: '',
        interaction_preferences: ''
      }
    }
  },
  created() {
    this.ensureSession()
  },
  beforeDestroy() {
    if (this.pollingTimer) {
      clearInterval(this.pollingTimer)
    }
  },
  methods: {
    async ensureSession() {
      if (this.sessionId) return
      const cachedSessionId = window.localStorage.getItem('teacherAgentSessionId')
      if (cachedSessionId) {
        try {
          const session = await fetchTeacherSession(cachedSessionId)
          this.sessionId = cachedSessionId
          this.hydrateSession(session)
          return
        } catch (error) {
          window.localStorage.removeItem('teacherAgentSessionId')
        }
      }
      if (this.sessionPromise) {
        await this.sessionPromise
        return
      }
      this.sessionPromise = createTeacherSession()
      try {
        const response = await this.sessionPromise
        this.sessionId = response.session_id
        window.localStorage.setItem('teacherAgentSessionId', this.sessionId)
      } finally {
        this.sessionPromise = null
      }
    },
    handleFieldUpdate({ field, value }) {
      this.intentForm = {
        ...this.intentForm,
        [field]: value
      }
    },
    appendMessageDraft(text) {
      this.messageDraft = [this.messageDraft, text].filter(Boolean).join('\n')
    },
    appendFollowupDraft(text) {
      this.followupDraft = [this.followupDraft, text].filter(Boolean).join('\n')
    },
    buildClarifyText() {
      const sections = [
        `主题：${this.intentForm.topic}`,
        `学科：${this.intentForm.subject}`,
        `年级：${this.intentForm.grade_level}`,
        `时长：${this.intentForm.lesson_duration}`,
        `教学目标：${this.intentForm.teaching_goals}`,
        `知识点：${this.intentForm.key_points}`,
        `重点难点：${this.intentForm.difficult_points}`,
        `风格要求：${this.intentForm.style_requirements}`,
        `互动偏好：${this.intentForm.interaction_preferences}`,
        `整体描述：${this.messageDraft}`
      ]
      return sections.filter(item => !item.endsWith('：')).join('\n')
    },
    applyIntent(intent) {
      this.intentForm = {
        topic: intent.topic || '',
        subject: intent.subject || '',
        grade_level: intent.grade_level || '',
        lesson_duration: intent.lesson_duration || '',
        teaching_goals: arrayToLines(intent.teaching_goals),
        key_points: arrayToLines(intent.key_points),
        difficult_points: arrayToLines(intent.difficult_points),
        style_requirements: arrayToLines(intent.style_requirements),
        interaction_preferences: arrayToLines(intent.interaction_preferences)
      }
    },
    hydrateSession(session) {
      this.applyIntent(session.intent || {})
      this.messages = session.messages || []
      this.references = session.references || []
      this.retrievals = session.retrievals || []
      this.confirmationCard = session.confirmation_card || {}
      this.missingFields = session.missing_fields || []
      this.summaryText = session.summary_text || ''
      this.assistantSuggestions = session.assistant_suggestions || []
      this.readyToGenerate = !this.missingFields.length && !!(session.intent?.topic || this.intentForm.topic)
      this.lessonPlanPreview = session.generation?.lesson_plan_preview || ''
      this.interactiveHtml = session.generation?.interactive_html || ''
      this.pptTask = session.generation?.ppt_task || {}
      this.revisionNote = session.last_revision_note || ''
      this.startPptPolling()
    },
    async runClarify(userInput) {
      await this.ensureSession()
      if (!userInput.trim()) {
        this.$message.warning('请先填写至少一部分教学需求')
        return
      }
      this.clarifying = true
      this.messages.push({ role: 'user', content: userInput })
      try {
        const response = await clarifyTeacherIntent({
          session_id: this.sessionId,
          user_input: userInput
        })
        this.messages.push({ role: 'assistant', content: response.assistant_message })
        this.applyIntent(response.intent)
        this.missingFields = response.missing_fields || []
        this.readyToGenerate = !!response.ready_to_generate
        this.confirmationCard = response.confirmation_card || {}
        this.summaryText = response.summary_text || ''
        this.assistantSuggestions = response.assistant_suggestions || []
      } catch (error) {
        this.$message.error(error.response?.data?.detail || '需求澄清失败')
      } finally {
        this.clarifying = false
      }
    },
    async handleClarify() {
      await this.runClarify(this.buildClarifyText())
    },
    async submitFollowupClarify() {
      const draft = this.followupDraft.trim()
      if (!draft) {
        this.$message.warning('请先输入本轮补充或修改内容')
        return
      }
      await this.runClarify(draft)
      this.followupDraft = ''
    },
    async handleUpload({ files, purpose }) {
      await this.ensureSession()
      this.uploading = true
      try {
        for (const file of files) {
          const response = await uploadTeacherReference(this.sessionId, file, purpose)
          this.references = [...this.references, response]
        }
        this.$message.success('资料上传并解析完成')
      } catch (error) {
        this.$message.error(error.response?.data?.detail || '资料上传失败')
      } finally {
        this.uploading = false
      }
    },
    async handleGenerate() {
      if (!this.readyToGenerate) {
        this.$message.warning('请先完成需求澄清，补齐必要字段')
        return
      }
      this.generating = true
      try {
        const response = await generateTeacherAssets({
          session_id: this.sessionId,
          regenerate_ppt: true,
          regenerate_lesson_plan: true,
          regenerate_interactive: true,
          revision_note: ''
        })
        this.consumeGenerationResponse(response)
        this.$message.success('课件初稿已生成')
      } catch (error) {
        this.$message.error(error.response?.data?.detail || '生成失败')
      } finally {
        this.generating = false
      }
    },
    async handleRevise() {
      if (!this.revisionNote.trim()) {
        this.$message.warning('请先填写修改意见')
        return
      }
      this.generating = true
      try {
        const response = await reviseTeacherAssets({
          session_id: this.sessionId,
          revision_note: this.revisionNote
        })
        this.consumeGenerationResponse(response)
        this.$message.success('已根据修改意见重新生成')
      } catch (error) {
        this.$message.error(error.response?.data?.detail || '再生成失败')
      } finally {
        this.generating = false
      }
    },
    consumeGenerationResponse(response) {
      this.lessonPlanPreview = response.lesson_plan_preview || ''
      this.interactiveHtml = response.interactive_html || ''
      this.references = response.references || this.references
      this.retrievals = response.retrievals || []
      this.pptTask = response.ppt_task || {}
      this.startPptPolling()
    },
    startPptPolling() {
      if (this.pollingTimer) clearInterval(this.pollingTimer)
      if (!this.pptTask.sid || !['building', 'pending'].includes(this.pptTask.status)) {
        return
      }
      this.pollingTimer = setInterval(() => {
        this.refreshPptStatus()
      }, 8000)
    },
    async refreshPptStatus() {
      if (!this.pptTask.sid) return
      try {
        const response = await fetchTeacherPptStatus(this.pptTask.sid)
        this.pptTask = { ...this.pptTask, ...response }
        if (!['building', 'pending'].includes(this.pptTask.status) && this.pollingTimer) {
          clearInterval(this.pollingTimer)
          this.pollingTimer = null
        }
      } catch (error) {
        if (this.pollingTimer) {
          clearInterval(this.pollingTimer)
          this.pollingTimer = null
        }
      }
    },
    downloadPpt() {
      if (!this.pptTask.download_url) {
        this.$message.warning('PPT 尚未生成完成')
        return
      }
      window.open(this.pptTask.download_url, '_blank')
    },
    async downloadLessonPlan() {
      if (!this.sessionId) return
      try {
        const response = await downloadTeacherLessonPlan(this.sessionId)
        this.saveBlob(response.data, 'lesson-plan.docx')
      } catch (error) {
        this.$message.error(error.response?.data?.detail || '下载教案失败')
      }
    },
    async downloadInteractive() {
      if (!this.sessionId) return
      try {
        const response = await downloadTeacherInteractive(this.sessionId)
        this.saveBlob(response.data, 'interactive-content.html')
      } catch (error) {
        this.$message.error(error.response?.data?.detail || '下载互动内容失败')
      }
    },
    saveBlob(blob, filename) {
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    },
    resetWorkspace() {
      this.sessionId = ''
      this.sessionPromise = null
      window.localStorage.removeItem('teacherAgentSessionId')
      this.messageDraft = ''
      this.followupDraft = ''
      this.revisionNote = ''
      this.readyToGenerate = false
      this.missingFields = []
      this.messages = []
      this.references = []
      this.retrievals = []
      this.summaryText = ''
      this.assistantSuggestions = []
      this.confirmationCard = {}
      this.lessonPlanPreview = ''
      this.interactiveHtml = ''
      this.pptTask = {}
      this.intentForm = {
        topic: '',
        subject: '',
        grade_level: '',
        lesson_duration: '',
        teaching_goals: '',
        key_points: '',
        difficult_points: '',
        style_requirements: '',
        interaction_preferences: ''
      }
      if (this.pollingTimer) {
        clearInterval(this.pollingTimer)
        this.pollingTimer = null
      }
      this.ensureSession()
    }
  }
}
</script>

<style scoped>
.teacher-agent-page {
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.16), transparent 32%),
    radial-gradient(circle at bottom right, rgba(15, 118, 110, 0.14), transparent 26%),
    linear-gradient(180deg, #eef4fb 0%, #f7fbff 52%, #eff5fb 100%);
  padding: 16px 18px 18px;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(204, 218, 235, 0.9);
  border-radius: 28px;
  padding: 18px 20px;
  box-shadow: 0 16px 45px rgba(15, 23, 42, 0.08);
}

.hero-tag {
  display: inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero h1 {
  margin-top: 10px;
  color: #16324f;
  font-size: 28px;
  line-height: 1.15;
}

.hero p {
  margin-top: 10px;
  max-width: 760px;
  color: #526272;
  line-height: 1.6;
}

.hero-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.workspace-grid {
  display: grid;
  grid-template-columns: 1.02fr 0.95fr 1.08fr;
  gap: 14px;
  margin-top: 12px;
  align-items: start;
  height: calc(100vh - 150px);
}

.workspace-card {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(204, 218, 235, 0.9);
  border-radius: 28px;
  padding: 14px;
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.07);
  min-height: 0;
  overflow: hidden;
}

.left-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
}

.middle-card,
.right-card {
  height: 100%;
  overflow-y: auto;
  padding-right: 10px;
}

@media (max-width: 1360px) {
  .teacher-agent-page {
    overflow: auto;
  }

  .workspace-grid {
    grid-template-columns: 1fr;
    height: auto;
  }

  .workspace-card,
  .left-card,
  .middle-card,
  .right-card {
    height: auto;
    overflow: visible;
    padding-right: 14px;
  }
}
</style>
