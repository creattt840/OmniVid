const TOKEN_KEY = 'omnivid_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}

export function authHeaders() {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export function parseApiError(err) {
  const detail = err?.response?.data?.detail ?? err?.detail
  if (typeof detail === 'object' && detail !== null) {
    return {
      message: detail.error || detail.message || '请求失败',
      code: detail.code || null,
    }
  }
  return { message: detail || err?.message || '请求失败', code: null }
}
