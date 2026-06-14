import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 120000 })

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
  return api.post('/subtitles/translate', { url, target_lang: targetLang, format }, {
    responseType: 'blob',
    timeout: 600000,
  })
}

export async function getDirectUrl(url, formatId) {
  const { data } = await api.post('/direct-url', { url, format_id: formatId })
  return data
}

export async function healthCheck() {
  const { data } = await api.get('/health')
  return data
}
