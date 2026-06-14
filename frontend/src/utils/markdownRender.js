function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function inlineFormat(text) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
}

/** 将 AI 输出的 Markdown 转为 HTML（标题、引用、列表、段落） */
export function renderMarkdown(md) {
  if (!md) return ''

  const lines = md.split('\n')
  const html = []
  let inList = false
  let inBlockquote = false

  const closeList = () => {
    if (inList) {
      html.push('</ul>')
      inList = false
    }
  }

  const closeBlockquote = () => {
    if (inBlockquote) {
      html.push('</blockquote>')
      inBlockquote = false
    }
  }

  for (const line of lines) {
    const trimmed = line.trim()

    if (!trimmed) {
      closeList()
      closeBlockquote()
      continue
    }

    const headingMatch = trimmed.match(/^(#{1,3})\s+(.+)$/)
    if (headingMatch) {
      closeList()
      closeBlockquote()
      const level = headingMatch[1].length
      const tag = level === 1 ? 'h1' : level === 2 ? 'h2' : 'h3'
      html.push(`<${tag}>${inlineFormat(headingMatch[2])}</${tag}>`)
      continue
    }

    if (trimmed.startsWith('> ')) {
      closeList()
      if (!inBlockquote) {
        html.push('<blockquote>')
        inBlockquote = true
      }
      html.push(`<p>${inlineFormat(trimmed.slice(2))}</p>`)
      continue
    }

    closeBlockquote()

    if (/^[-*]\s+/.test(trimmed)) {
      if (!inList) {
        html.push('<ul>')
        inList = true
      }
      html.push(`<li>${inlineFormat(trimmed.replace(/^[-*]\s+/, ''))}</li>`)
      continue
    }

    closeList()
    html.push(`<p>${inlineFormat(trimmed)}</p>`)
  }

  closeList()
  closeBlockquote()
  return html.join('')
}
