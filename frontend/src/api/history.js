import axios from 'axios'
import { authHeaders, parseApiError } from './authStorage.js'

const api = axios.create({ baseURL: '/api', timeout: 60000 })

api.interceptors.request.use((config) => {
  const headers = authHeaders()
  if (headers.Authorization) {
    config.headers = { ...config.headers, ...headers }
  }
  return config
})

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

  if (buffer.trim()) {
    for (const line of buffer.split('\n')) processLine(line)
  }
}

export async function fetchHistory() {
  try {
    const { data } = await api.get('/analysis-history')
    return data
  } catch (err) {
    throw parseApiError(err)
  }
}

export async function saveHistory(item) {
  try {
    const { data } = await api.post('/analysis-history', {
      url: item.url,
      source: item.source || (item.url?.startsWith('local://') ? 'local' : 'url'),
      title: item.title,
      platform: item.platform,
      thumbnail: item.thumbnail,
      summary: item.summary,
      mindmap: item.mindmap,
      segments: item.segments,
      article: item.article,
      chatHistory: item.chatHistory,
      transcriptSource: item.transcriptSource,
      partial: item.partial || false,
    })
    return data
  } catch (err) {
    throw parseApiError(err)
  }
}

export function chatHistoryAnalyze(historyId, message, onEvent) {
  return consumeSSE(
    `/api/analysis-history/${historyId}/chat`,
    { method: 'POST', body: JSON.stringify({ message }) },
    onEvent,
  )
}

export function rewriteHistoryAnalyze(historyId, onEvent) {
  return consumeSSE(`/api/analysis-history/${historyId}/rewrite`, { method: 'GET' }, onEvent)
}

export async function deleteHistory(id) {
  try {
    const { data } = await api.delete(`/analysis-history/${id}`)
    return data
  } catch (err) {
    throw parseApiError(err)
  }
}

export async function clearHistory() {
  try {
    const { data } = await api.delete('/analysis-history')
    return data
  } catch (err) {
    throw parseApiError(err)
  }
}
