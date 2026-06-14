/** 将 "MM:SS" 或 "HH:MM:SS" 解析为秒数 */
export function parseTimeString(timeStr) {
  if (!timeStr) return 0
  const parts = String(timeStr).trim().split(':').map(Number)
  if (parts.some(Number.isNaN)) return 0
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2]
  if (parts.length === 2) return parts[0] * 60 + parts[1]
  return parts[0] || 0
}

/** 构建带时间戳的原视频链接 */
export function buildVideoUrlWithTimestamp(videoUrl, seconds) {
  if (!videoUrl || seconds <= 0) return videoUrl
  try {
    const u = new URL(videoUrl)
    if (u.hostname.includes('youtube.com') || u.hostname.includes('youtu.be')) {
      u.searchParams.set('t', String(Math.floor(seconds)))
      return u.toString()
    }
    if (u.hostname.includes('bilibili.com')) {
      u.searchParams.set('t', String(Math.floor(seconds)))
      return u.toString()
    }
    return `${videoUrl}${videoUrl.includes('?') ? '&' : '?'}t=${Math.floor(seconds)}`
  } catch {
    return videoUrl
  }
}
