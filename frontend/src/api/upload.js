/**
 * 本地视频/音频上传（multipart，带进度回调）
 * 大文件使用 XMLHttpRequest 以支持 upload progress
 */

const API_BASE = import.meta.env.DEV ? 'http://localhost:8000' : ''

function parseErrorResponse(xhr) {
  try {
    const data = JSON.parse(xhr.responseText || '{}')
    const detail = data.detail
    if (typeof detail === 'object' && detail?.error) return detail.error
    if (typeof detail === 'string') return detail
    return data.error || xhr.statusText || '上传失败'
  } catch {
    return xhr.statusText || '上传失败'
  }
}

export function uploadLocalFile(mediaFile, subtitleFile = null, onProgress = null) {
  return new Promise((resolve, reject) => {
    const form = new FormData()
    form.append('media', mediaFile)
    if (subtitleFile) {
      form.append('subtitle', subtitleFile)
    }

    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API_BASE}/api/upload`)
    xhr.timeout = 600000 // 10 min

    if (onProgress) {
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          onProgress(Math.round((e.loaded / e.total) * 100))
        }
      }
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText))
        } catch {
          reject(new Error('服务器响应格式错误'))
        }
      } else {
        reject(new Error(parseErrorResponse(xhr)))
      }
    }

    xhr.onerror = () => reject(new Error('网络错误，上传失败'))
    xhr.ontimeout = () => reject(new Error('上传超时，请检查网络或减小文件体积'))
    xhr.send(form)
  })
}

export function getUploadStreamUrl(fileId) {
  return `${API_BASE}/api/upload/${fileId}/stream`
}
