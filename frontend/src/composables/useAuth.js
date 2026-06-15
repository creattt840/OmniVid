import { ref, computed } from 'vue'
import { login as apiLogin, register as apiRegister, fetchMe } from '../api/auth.js'
import { getToken, setToken } from '../api/authStorage.js'

const user = ref(null)
const loading = ref(false)
const initialized = ref(false)

export function useAuth() {
  const isLoggedIn = computed(() => !!user.value)
  const isVip = computed(() => !!user.value?.is_vip)

  async function initAuth() {
    if (initialized.value) return
    initialized.value = true
    if (!getToken()) return
    try {
      loading.value = true
      const res = await fetchMe()
      if (res.success) user.value = res.data
    } catch {
      setToken(null)
      user.value = null
    } finally {
      loading.value = false
    }
  }

  async function login(email, password) {
    const res = await apiLogin(email, password)
    if (res.success) {
      setToken(res.data.token)
      user.value = res.data.user
    }
    return res
  }

  async function register(email, password) {
    const res = await apiRegister(email, password)
    if (res.success) {
      setToken(res.data.token)
      user.value = res.data.user
    }
    return res
  }

  async function refreshUser() {
    if (!getToken()) return
    const res = await fetchMe()
    if (res.success) user.value = res.data
    return res
  }

  function logout() {
    setToken(null)
    user.value = null
  }

  return {
    user,
    loading,
    isLoggedIn,
    isVip,
    initAuth,
    login,
    register,
    refreshUser,
    logout,
  }
}
