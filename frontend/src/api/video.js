import axios from 'axios'
import { authHeaders } from './authStorage.js'

const api = axios.create({ baseURL: '/api', timeout: 120000 })

api.interceptors.request.use((config) => {
  const headers = authHeaders()
  if (headers.Authorization) {
    config.headers = { ...config.headers, ...headers }
  }
  return config
})

export async function parseVideo(url) {
  const { data } = await api.post('/parse', { url })
  return data
}

export async function downloadViaServer(url, formatId) {
  return api.post('/download', { url, format_id: formatId }, {
    responseType: 'blob',
    timeout: 600000,
  })
}

export async function downloadSubtitles(url, format = 'srt') {
  return api.post('/subtitles/download', { url, format }, {
    responseType: 'blob',
    timeout: 600000,
  })
}

export async function translateSubtitles(url, targetLang = 'en', format = 'srt') {
  try {
    return await api.post('/subtitles/translate', { url, target_lang: targetLang, format }, {
      responseType: 'blob',
      timeout: 600000,
    })
  } catch (err) {
    const detail = err.response?.data?.detail
    const error = new Error(typeof detail === 'object' ? detail.error : (detail || err.message || '翻译失败'))
    error.code = typeof detail === 'object' ? detail.code : null
    throw error
  }
}

export async function getDirectUrl(url, formatId) {
  const { data } = await api.post('/direct-url', { url, format_id: formatId })
  return data
}

export async function healthCheck() {
  const { data } = await api.get('/health')
  return data
}

/** 触发浏览器保存 Blob 文件 */
export function triggerBlobDownload(blob, filename) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

/**
 * 尝试通过 fetch 直链下载（跨域 CDN 不支持 <a download>，需先拉取 Blob）
 * @returns {boolean} 是否成功
 */
export async function downloadFromDirectUrl(directUrl, filename) {
  try {
    const resp = await fetch(directUrl)
    if (!resp.ok) return false
    const blob = await resp.blob()
    triggerBlobDownload(blob, filename)
    return true
  } catch {
    return false
  }
}

/** 从 Content-Disposition 响应头解析文件名 */
export function parseFilenameFromDisposition(contentDisposition, fallback = 'video.mp4') {
  if (!contentDisposition) return fallback
  const match = contentDisposition.match(/filename\*?=(?:UTF-8'')?([^;\n]+)/i)
  if (!match) return fallback
  return decodeURIComponent(match[1].replace(/"/g, ''))
}
