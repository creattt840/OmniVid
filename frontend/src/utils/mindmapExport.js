import { toPng, toSvg } from 'html-to-image'
import { Transformer } from 'markmap-lib'

const transformer = new Transformer()

export function sanitizeFilename(name, ext) {
  const safe = (name || 'mindmap').replace(/[<>:"/\\|?*\x00-\x1f]/g, '_').trim().slice(0, 80)
  return `${safe || 'mindmap'}.${ext}`
}

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function downloadDataUrl(dataUrl, filename) {
  const a = document.createElement('a')
  a.href = dataUrl
  a.download = filename
  a.click()
}

async function dataUrlToBlob(dataUrl) {
  const res = await fetch(dataUrl)
  return res.blob()
}

function withTimeout(promise, ms, message) {
  return Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error(message)), ms)),
  ])
}

function decodeHtmlEntities(text) {
  if (!text || !/&[#\w]+;/.test(text)) return text
  const el = document.createElement('textarea')
  el.innerHTML = text
  return el.value
}

function plainNodeText(content) {
  if (!content) return ''
  const stripped = content.replace(/<[^>]+>/g, '')
  return decodeHtmlEntities(stripped).trim()
}

/** 从 markmap 树结构重建带层级的 Markdown 标题 */
function nodeToMarkdown(node, depth = 1) {
  const lines = []
  const text = plainNodeText(node.content)
  if (text) {
    const level = Math.min(Math.max(depth, 1), 6)
    lines.push(`${'#'.repeat(level)} ${text}`)
  }
  const childDepth = text ? depth + 1 : depth
  for (const child of node.children || []) {
    const block = nodeToMarkdown(child, childDepth)
    if (block) lines.push(block)
  }
  return lines.join('\n\n')
}

export function buildMindmapMarkdown(content) {
  if (!content?.trim()) return ''
  try {
    const { root } = transformer.transform(content)
    const md = nodeToMarkdown(root, 1)
    return md || content.trim()
  } catch {
    return content.trim()
  }
}

function getExportContainer(containerEl, svgEl) {
  if (containerEl && containerEl.getBoundingClientRect().width > 0) {
    return containerEl
  }
  return null
}

async function captureContainer(containerEl, options) {
  return withTimeout(
    options.format === 'svg'
      ? toSvg(containerEl, { backgroundColor: '#f8fafc', cacheBust: true })
      : toPng(containerEl, {
          backgroundColor: '#f8fafc',
          pixelRatio: options.pixelRatio || 3,
          cacheBust: true,
        }),
    30000,
    `${options.format.toUpperCase()} 导出超时，请稍后重试`,
  )
}

/** 离屏包装 SVG，供容器不可见时截图 */
async function captureFromSvg(svgEl, options) {
  const wrapper = document.createElement('div')
  wrapper.style.cssText =
    'position:fixed;left:0;top:0;z-index:-9999;background:#f8fafc;padding:40px;pointer-events:none;'
  const clone = svgEl.cloneNode(true)
  clone.style.width = `${Math.max(svgEl.getBoundingClientRect().width, 800)}px`
  clone.style.height = `${Math.max(svgEl.getBoundingClientRect().height, 400)}px`
  wrapper.appendChild(clone)
  document.body.appendChild(wrapper)
  try {
    return await captureContainer(wrapper, options)
  } finally {
    document.body.removeChild(wrapper)
  }
}

export function exportMindmapMarkdown(content, title) {
  const md = buildMindmapMarkdown(content)
  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' })
  downloadBlob(blob, sanitizeFilename(`${title}-思维导图`, 'md'))
}

export async function exportMindmapSvg(containerEl, svgEl, title) {
  const target = getExportContainer(containerEl, svgEl)
  const dataUrl = target
    ? await captureContainer(target, { format: 'svg' })
    : await captureFromSvg(svgEl, { format: 'svg' })
  const blob = await dataUrlToBlob(dataUrl)
  downloadBlob(blob, sanitizeFilename(`${title}-思维导图`, 'svg'))
}

export async function exportMindmapPng(containerEl, svgEl, title, pixelRatio = 3) {
  const target = getExportContainer(containerEl, svgEl)
  const dataUrl = target
    ? await captureContainer(target, { format: 'png', pixelRatio })
    : await captureFromSvg(svgEl, { format: 'png', pixelRatio })
  downloadDataUrl(dataUrl, sanitizeFilename(`${title}-思维导图`, 'png'))
}
