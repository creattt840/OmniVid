import { authApi } from './auth.js'
import { parseApiError } from './authStorage.js'

export async function createCheckout() {
  try {
    const { data } = await authApi.post('/billing/checkout')
    return data
  } catch (err) {
    throw parseApiError(err)
  }
}
