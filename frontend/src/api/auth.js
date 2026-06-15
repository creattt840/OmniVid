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

export async function register(email, password) {
  try {
    const { data } = await api.post('/auth/register', { email, password })
    return data
  } catch (err) {
    throw parseApiError(err)
  }
}

export async function login(email, password) {
  try {
    const { data } = await api.post('/auth/login', { email, password })
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
