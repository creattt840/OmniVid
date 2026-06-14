function formatSrtTime(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  const ms = Math.round((seconds % 1) * 1000)
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')},${String(ms).padStart(3, '0')}`
}

function formatVttTime(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${s.toFixed(3).padStart(6, '0')}`
}

function formatTxtTime(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

export function segmentsToSrt(segments) {
  return segments.map((seg, i) => {
    const start = formatSrtTime(seg.start)
    const end = formatSrtTime(Math.max(seg.end, seg.start + 0.001))
    return `${i + 1}\n${start} --> ${end}\n${seg.text}\n`
  }).join('\n')
}

export function segmentsToVtt(segments) {
  const lines = ['WEBVTT', '']
  for (const seg of segments) {
    const start = formatVttTime(seg.start)
    const end = formatVttTime(Math.max(seg.end, seg.start + 0.001))
    lines.push(`${start} --> ${end}`, seg.text, '')
  }
  return lines.join('\n')
}

export function segmentsToTxt(segments) {
  return segments.map((seg) => `[${formatTxtTime(seg.start)}] ${seg.text}`).join('\n')
}

export function sanitizeFilename(name, ext) {
  const safe = (name || 'subtitle').replace(/[<>:"/\\|?*\x00-\x1f]/g, '_').trim().slice(0, 80)
  return `${safe || 'subtitle'}.${ext}`
}

export function downloadSubtitleContent(content, title, format) {
  const mimeTypes = {
    srt: 'application/x-subrip;charset=utf-8',
    vtt: 'text/vtt;charset=utf-8',
    txt: 'text/plain;charset=utf-8',
  }
  const blob = new Blob([content], { type: mimeTypes[format] || 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = sanitizeFilename(title, format)
  a.click()
  URL.revokeObjectURL(url)
}

export function downloadSegments(segments, title, format) {
  const converters = { srt: segmentsToSrt, vtt: segmentsToVtt, txt: segmentsToTxt }
  const content = converters[format](segments)
  downloadSubtitleContent(content, title, format)
}
