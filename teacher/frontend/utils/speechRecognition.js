export function extractSpeechResult(event) {
  if (!event || !event.results || !event.results.length) {
    return {
      transcript: '',
      isFinal: false
    }
  }
  const index = typeof event.resultIndex === 'number'
    ? event.resultIndex
    : event.results.length - 1
  const safeIndex = Math.min(index, event.results.length - 1)
  const result = event.results[safeIndex]
  if (!result || !result[0]) {
    return {
      transcript: '',
      isFinal: false
    }
  }
  return {
    transcript: result[0].transcript || '',
    isFinal: !!result.isFinal
  }
}

export function extractSpeechTranscript(event) {
  return extractSpeechResult(event).transcript
}

export function mergeSpeechIntoDraft(baseText, transcript) {
  const safeBase = (baseText || '').replace(/\s+$/, '')
  const safeTranscript = (transcript || '').trim()
  if (!safeBase) {
    return safeTranscript
  }
  if (!safeTranscript) {
    return safeBase
  }
  return `${safeBase}\n${safeTranscript}`
}

export function startBrowserSpeechRecognition({
  lang = 'zh-CN',
  onStart,
  onResult,
  onError,
  onEnd
} = {}) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SpeechRecognition) {
    throw new Error('当前浏览器不支持语音输入，请使用 Chrome 或 Edge 桌面版')
  }

  const recognition = new SpeechRecognition()
  recognition.lang = lang
  recognition.continuous = false
  // Chrome / Edge 下保留中间结果更稳定，再由调用方决定是否只消费最终结果。
  recognition.interimResults = true

  recognition.onstart = () => {
    if (onStart) onStart()
  }

  recognition.onresult = event => {
    const { transcript, isFinal } = extractSpeechResult(event)
    if (transcript && onResult) {
      onResult(transcript, {
        isFinal,
        event
      })
    }
  }

  recognition.onerror = event => {
    if (onError) onError(event)
  }

  recognition.onend = () => {
    if (onEnd) onEnd()
  }

  recognition.start()
  return recognition
}
