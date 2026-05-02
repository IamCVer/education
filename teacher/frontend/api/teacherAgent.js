import request from '@/utils/request'

export function createTeacherSession() {
  return request.post('/api/v1/teacher-agent/session')
}

export function fetchTeacherSession(sessionId) {
  return request.get(`/api/v1/teacher-agent/session/${sessionId}`)
}

export function clarifyTeacherIntent(payload) {
  return request.post('/api/v1/teacher-agent/clarify', payload)
}

export function uploadTeacherReference(sessionId, file, purpose) {
  const formData = new FormData()
  formData.append('session_id', sessionId)
  formData.append('purpose', purpose || '')
  formData.append('file', file)
  return request.post('/api/v1/teacher-agent/upload', formData)
}

export function generateTeacherAssets(payload) {
  return request.post('/api/v1/teacher-agent/generate', payload)
}

export function reviseTeacherAssets(payload) {
  return request.post('/api/v1/teacher-agent/revise', payload)
}

export function fetchTeacherPptStatus(sid) {
  return request.get(`/api/v1/teacher-agent/ppt/${sid}`)
}

export function downloadTeacherLessonPlan(sessionId) {
  return request.get(`/api/v1/teacher-agent/download/lesson-plan/${sessionId}`, {
    responseType: 'blob'
  })
}

export function downloadTeacherInteractive(sessionId) {
  return request.get(`/api/v1/teacher-agent/download/interactive/${sessionId}`, {
    responseType: 'blob'
  })
}
