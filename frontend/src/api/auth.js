import axios from 'axios'
import { authHeaders, parseApiError } from './authStorage.js'

const api = axios.create({ baseURL: '/api', timeout: 60000 })

api.interceptors.request.use((config) => {
  const headers = authHeaders()
  if (headers.Authorization) {
    config.headers = { ...config.headers, ...headers }
  }
  return config
})

export async function sendCode(email, purpose) {
  try {
    const { data } = await api.post('/auth/send-code', { email, purpose })
    return data
  } catch (err) {
    throw parseApiError(err)
  }
}

export async function register(email, password, code) {
  try {
    const { data } = await api.post('/auth/register', { email, password, code })
    return data
  } catch (err) {
    throw parseApiError(err)
  }
}

export async function login(email, { password, code } = {}) {
  try {
    const payload = { email }
    if (code) payload.code = code
    else payload.password = password
    const { data } = await api.post('/auth/login', payload)
    return data
  } catch (err) {
    throw parseApiError(err)
  }
}

export async function resetPassword(email, code, newPassword) {
  try {
    const { data } = await api.post('/auth/reset-password', {
      email,
      code,
      new_password: newPassword,
    })
    return data
  } catch (err) {
    throw parseApiError(err)
  }
}

export async function fetchMe() {
  try {
    const { data } = await api.get('/auth/me')
    return data
  } catch (err) {
    throw parseApiError(err)
  }
}

export { api as authApi }
