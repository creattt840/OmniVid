import { sanitizeFilename } from './subtitleExport.js'
import { renderMarkdown } from './markdownRender.js'

function buildMarkdown({ title, platform, url, summary, mindmap }) {
  const lines = [`# ${title || '视频分析笔记'}`, '']
  if (platform) lines.push(`> 平台：${platform}`)
  if (url) lines.push(`> 链接：${url}`)
  lines.push(`> 导出时间：${new Date().toLocaleString('zh-CN')}`, '')

  if (summary?.summary) {
    lines.push('## 摘要', '', summary.summary, '')
  }
  if (summary?.highlights?.length) {
    lines.push('## 核心要点', '')
    summary.highlights.forEach((item, i) => lines.push(`${i + 1}. ${item}`))
    lines.push('')
  }
  if (summary?.chapters?.length) {
    lines.push('## 章节大纲', '')
    summary.chapters.forEach((ch) => {
      lines.push(`### ${ch.time || ''} ${ch.title || ''}`.trim())
      if (ch.summary) lines.push('', ch.summary)
      lines.push('')
    })
  }
  if (summary?.terms?.length) {
    lines.push('## 术语解释', '')
    summary.terms.forEach((t) => {
      lines.push(`**${t.term}**：${t.definition}`)
    })
    lines.push('')
  }
  if (mindmap) {
    lines.push('## 思维导图', '', '```markdown', mindmap, '```', '')
  }
  return lines.join('\n')
}

function buildPrintHtml({ title, platform, url, summary, mindmap, article }) {
  const esc = (s) => String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  const highlights = (summary?.highlights || [])
    .map((h, i) => `<li>${esc(h)}</li>`).join('')
  const chapters = (summary?.chapters || [])
    .map((ch) => `<div class="chapter"><strong>${esc(ch.time)} ${esc(ch.title)}</strong><p>${esc(ch.summary)}</p></div>`)
    .join('')
  const terms = (summary?.terms || [])
    .map((t) => `<p><strong>${esc(t.term)}</strong>：${esc(t.definition)}</p>`).join('')

  return `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${esc(title)}</title>
<style>
  body { font-family: -apple-system, "PingFang SC", sans-serif; max-width: 720px; margin: 40px auto; padding: 0 24px; color: #1f2937; line-height: 1.7; }
  h1 { font-size: 22px; border-bottom: 2px solid #6366f1; padding-bottom: 8px; }
  h2 { font-size: 16px; color: #6366f1; margin-top: 28px; }
  .meta { color: #6b7280; font-size: 13px; margin-bottom: 24px; }
  .chapter { background: #f9fafb; border-radius: 8px; padding: 12px; margin: 8px 0; }
  .article { white-space: pre-wrap; }
  pre { background: #f3f4f6; padding: 12px; border-radius: 8px; font-size: 12px; overflow-x: auto; }
</style></head><body>
<h1>${esc(title)}</h1>
<div class="meta">${platform ? `平台：${esc(platform)}<br>` : ''}${url ? `链接：${esc(url)}<br>` : ''}导出时间：${new Date().toLocaleString('zh-CN')}</div>
${summary?.summary ? `<h2>摘要</h2><p>${esc(summary.summary)}</p>` : ''}
${highlights ? `<h2>核心要点</h2><ol>${highlights}</ol>` : ''}
${chapters ? `<h2>章节大纲</h2>${chapters}` : ''}
${terms ? `<h2>术语解释</h2>${terms}` : ''}
${article ? `<h2>AI 改写文章</h2><div class="article">${renderMarkdown(article)}</div>` : ''}
${mindmap ? `<h2>思维导图</h2><pre>${esc(mindmap)}</pre>` : ''}
</body></html>`
}

export function downloadSummaryMarkdown({ title, platform, url, summary, mindmap }) {
  const content = buildMarkdown({ title, platform, url, summary, mindmap })
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  const blobUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = blobUrl
  a.download = sanitizeFilename(title || 'summary', 'md')
  a.click()
  URL.revokeObjectURL(blobUrl)
}

export function downloadSummaryPdf({ title, platform, url, summary, mindmap, article }) {
  const html = buildPrintHtml({ title, platform, url, summary, mindmap, article })
  const win = window.open('', '_blank')
  if (!win) {
    alert('请允许弹出窗口以导出 PDF')
    return
  }
  win.document.write(html)
  win.document.close()
  win.onload = () => {
    win.focus()
    win.print()
  }
}
