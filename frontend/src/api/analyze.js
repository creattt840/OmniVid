/**
 * SSE 流式请求工具
 */
async function consumeSSE(url, options, onEvent) {
  const resp = await fetch(url, {
    ...options,
    headers: {
      Accept: 'text/event-stream',
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    const detail = err.detail
    const msg = typeof detail === 'object' ? detail.error : (detail || resp.statusText)
    throw new Error(msg || '请求失败')
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          onEvent(JSON.parse(line.slice(6)))
        } catch { /* skip malformed */ }
      }
    }
  }
}

export async function startAnalyze(url) {
  const resp = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
  const data = await resp.json()
  if (!resp.ok) {
    const detail = data.detail
    throw new Error(typeof detail === 'object' ? detail.error : (detail || '分析失败'))
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
