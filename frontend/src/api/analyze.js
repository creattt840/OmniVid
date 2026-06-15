/**
 * SSE 流式请求工具
 */
import { authHeaders } from './authStorage.js'

async function consumeSSE(url, options, onEvent) {
  const resp = await fetch(url, {
    ...options,
    headers: {
      Accept: 'text/event-stream',
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...options?.headers,
    },
  })

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    const detail = err.detail
    const msg = typeof detail === 'object' ? detail.error : (detail || resp.statusText)
    const code = typeof detail === 'object' ? detail.code : null
    const error = new Error(msg || '请求失败')
    error.code = code
    throw error
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  function processLine(line) {
    if (line.startsWith('data: ')) {
      try {
        onEvent(JSON.parse(line.slice(6)))
      } catch { /* skip malformed */ }
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) processLine(line)
  }

  // 处理缓冲区剩余数据，避免最后一个 SSE 事件丢失导致卡住
  if (buffer.trim()) {
    for (const line of buffer.split('\n')) processLine(line)
  }
}

export async function startAnalyze({ url, fileId } = {}) {
  const body = url ? { url } : { file_id: fileId }
  const resp = await fetch('/api/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(body),
  })
  const data = await resp.json()
  if (!resp.ok) {
    const detail = data.detail
    const error = new Error(typeof detail === 'object' ? detail.error : (detail || '分析失败'))
    error.code = typeof detail === 'object' ? detail.code : null
    throw error
  }
  return data
}

export function streamAnalyze(sessionId, onEvent) {
  return consumeSSE(`/api/analyze/${sessionId}/stream`, { method: 'GET' }, onEvent)
}

export function chatAnalyze(sessionId, message, onEvent) {
  return consumeSSE(
    `/api/analyze/${sessionId}/chat`,
    { method: 'POST', body: JSON.stringify({ message }) },
    onEvent,
  )
}

export function rewriteAnalyze(sessionId, onEvent) {
  return consumeSSE(`/api/analyze/${sessionId}/rewrite`, { method: 'GET' }, onEvent)
}
