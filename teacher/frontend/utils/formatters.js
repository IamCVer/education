export function linesToArray(value) {
  if (!value) return []
  return String(value)
    .split(/\n|,|，|;|；|、/)
    .map(item => item.trim())
    .filter(Boolean)
}

export function arrayToLines(value) {
  if (!Array.isArray(value)) return value || ''
  return value.join('\n')
}

export function humanizeMissingField(field) {
  const map = {
    topic: '教学主题',
    grade_level: '适用年级',
    lesson_duration: '课时/时长',
    teaching_goals: '教学目标',
    key_points: '核心知识点'
  }
  return map[field] || field
}

export function formatPptStatus(status) {
  const map = {
    building: '生成中',
    done: '已完成',
    finished: '已完成',
    fail: '失败',
    build_failed: '失败',
    failed: '失败',
    pending: '待提交'
  }
  return map[status] || status || '未知'
}
