const STORAGE_KEY = 'omnivid_history'
const MAX_ITEMS = 20

export function loadHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function saveHistoryItem(item) {
  const list = loadHistory().filter((h) => h.url !== item.url)
  list.unshift({
    id: item.id || crypto.randomUUID(),
    url: item.url,
    title: item.title,
    platform: item.platform,
    thumbnail: item.thumbnail,
    analyzedAt: item.analyzedAt || Date.now(),
    summary: item.summary || null,
    mindmap: item.mindmap || '',
  })
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(0, MAX_ITEMS)))
}

export function removeHistoryItem(id) {
  const list = loadHistory().filter((h) => h.id !== id)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

export function clearHistory() {
  localStorage.removeItem(STORAGE_KEY)
}
