<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="open"
        class="fixed inset-0 z-[300] flex items-center justify-center p-4 bg-black/40"
        @click.self="$emit('close')"
      >
        <div class="w-full max-w-md bg-bg-card rounded-2xl shadow-2xl border border-border overflow-hidden">
          <div class="px-6 pt-6 pb-4 border-b border-border-light">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-lg font-bold text-text-primary">
                {{ titleText }}
              </h2>
              <button
                type="button"
                class="w-8 h-8 rounded-lg hover:bg-surface-muted flex items-center justify-center cursor-pointer"
                aria-label="关闭"
                @click="$emit('close')"
              >
                <svg class="w-5 h-5 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div v-if="mode !== 'forgot'" class="flex gap-1 p-1 bg-surface-muted rounded-lg">
              <button
                type="button"
                class="flex-1 py-2 text-sm font-medium rounded-md transition-colors cursor-pointer"
                :class="mode === 'login' ? 'bg-bg-card text-primary shadow-sm' : 'text-text-secondary'"
                @click="switchMode('login')"
              >
                登录
              </button>
              <button
                type="button"
                class="flex-1 py-2 text-sm font-medium rounded-md transition-colors cursor-pointer"
                :class="mode === 'register' ? 'bg-bg-card text-primary shadow-sm' : 'text-text-secondary'"
                @click="switchMode('register')"
              >
                注册
              </button>
            </div>
          </div>

          <form class="px-6 py-5 space-y-4" @submit.prevent="handleSubmit">
            <div>
              <label class="block text-sm font-medium text-text-secondary mb-1.5">邮箱</label>
              <input
                v-model="email"
                type="email"
                required
                autocomplete="email"
                placeholder="you@example.com"
                class="w-full h-11 px-4 rounded-lg border border-border bg-bg-page text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>

            <div v-if="showCodeField">
              <label class="block text-sm font-medium text-text-secondary mb-1.5">验证码</label>
              <div class="flex gap-2">
                <input
                  v-model="code"
                  type="text"
                  inputmode="numeric"
                  pattern="[0-9]*"
                  maxlength="6"
                  required
                  autocomplete="one-time-code"
                  placeholder="6 位验证码"
                  class="flex-1 h-11 px-4 rounded-lg border border-border bg-bg-page text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
                <button
                  type="button"
                  class="shrink-0 h-11 px-4 rounded-lg border border-border text-sm font-medium transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                  :class="countdown > 0 ? 'text-text-muted bg-surface-muted' : 'text-primary hover:bg-primary/5'"
                  :disabled="sendingCode || countdown > 0 || !email.trim()"
                  @click="handleSendCode"
                >
                  {{ countdown > 0 ? `${countdown}s` : (sendingCode ? '发送中...' : '获取验证码') }}
                </button>
              </div>
            </div>

            <div v-if="showPasswordField">
              <label class="block text-sm font-medium text-text-secondary mb-1.5">
                {{ mode === 'forgot' ? '新密码' : '密码' }}
              </label>
              <input
                v-model="password"
                type="password"
                required
                minlength="6"
                :autocomplete="passwordAutocomplete"
                placeholder="至少 6 位"
                class="w-full h-11 px-4 rounded-lg border border-border bg-bg-page text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>

            <div v-if="mode === 'forgot'">
              <label class="block text-sm font-medium text-text-secondary mb-1.5">确认新密码</label>
              <input
                v-model="confirmPassword"
                type="password"
                required
                minlength="6"
                autocomplete="new-password"
                placeholder="再次输入新密码"
                class="w-full h-11 px-4 rounded-lg border border-border bg-bg-page text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>

            <p v-if="successMsg" class="text-sm text-green-600">{{ successMsg }}</p>
            <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

            <div class="space-y-2">
              <button
                type="submit"
                class="w-full h-11 rounded-lg bg-primary text-white font-semibold text-sm hover:bg-primary-dark transition-colors cursor-pointer disabled:opacity-60"
                :disabled="submitting"
              >
                {{ submitText }}
              </button>
              <div
                v-if="mode === 'login' && loginMethod === 'password'"
                class="flex justify-end"
              >
                <button
                  type="button"
                  class="text-sm text-text-muted hover:text-primary transition-colors cursor-pointer"
                  @click="switchMode('forgot')"
                >
                  忘记密码？
                </button>
              </div>
            </div>

            <div v-if="mode === 'login'" class="text-center text-sm pt-1">
              <button
                v-if="loginMethod === 'password'"
                type="button"
                class="text-primary hover:underline cursor-pointer"
                @click="switchLoginMethod('code')"
              >
                使用验证码登录
              </button>
              <button
                v-else
                type="button"
                class="text-primary hover:underline cursor-pointer"
                @click="switchLoginMethod('password')"
              >
                使用密码登录
              </button>
            </div>

            <div v-if="mode === 'forgot'" class="text-center">
              <button
                type="button"
                class="text-sm text-primary hover:underline cursor-pointer"
                @click="switchMode('login')"
              >
                返回登录
              </button>
            </div>
          </form>

          <p v-if="mode !== 'forgot'" class="px-6 pb-6 pt-1 text-xs text-text-muted text-center">
            登录后可使用 AI 视频分析，每个账号每日免费 10 次
          </p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { useAuth } from '../composables/useAuth.js'

const props = defineProps({
  open: Boolean,
  initialMode: { type: String, default: 'login' },
})

const emit = defineEmits(['close', 'success'])

const { login, register, sendCode, resetPassword } = useAuth()

const mode = ref(props.initialMode)
const loginMethod = ref('password')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const code = ref('')
const error = ref('')
const successMsg = ref('')
const submitting = ref(false)
const sendingCode = ref(false)
const countdown = ref(0)

let countdownTimer = null

const titleText = computed(() => {
  if (mode.value === 'forgot') return '重置密码'
  return mode.value === 'login' ? '登录 OmniVid' : '注册账号'
})

const showCodeField = computed(() => {
  if (mode.value === 'register' || mode.value === 'forgot') return true
  return mode.value === 'login' && loginMethod.value === 'code'
})

const showPasswordField = computed(() => {
  if (mode.value === 'register' || mode.value === 'forgot') return true
  return mode.value === 'login' && loginMethod.value === 'password'
})

const passwordAutocomplete = computed(() => {
  if (mode.value === 'forgot') return 'new-password'
  return mode.value === 'login' ? 'current-password' : 'new-password'
})

const submitText = computed(() => {
  if (submitting.value) return '处理中...'
  if (mode.value === 'forgot') return '重置密码'
  return mode.value === 'login' ? '登录' : '注册'
})

const codePurpose = computed(() => {
  if (mode.value === 'register') return 'register'
  if (mode.value === 'forgot') return 'reset_password'
  return 'login'
})

function clearCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  countdown.value = 0
}

function startCountdown(seconds = 60) {
  clearCountdown()
  countdown.value = seconds
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) clearCountdown()
  }, 1000)
}

function resetFormMessages() {
  error.value = ''
  successMsg.value = ''
}

function switchMode(next) {
  mode.value = next
  resetFormMessages()
  code.value = ''
  password.value = ''
  confirmPassword.value = ''
  if (next === 'login') loginMethod.value = 'password'
}

function switchLoginMethod(method) {
  loginMethod.value = method
  resetFormMessages()
  code.value = ''
  password.value = ''
}

watch(() => props.open, (val) => {
  if (val) {
    mode.value = props.initialMode === 'register' ? 'register' : 'login'
    loginMethod.value = 'password'
    resetFormMessages()
  } else {
    clearCountdown()
  }
})

watch(() => props.initialMode, (val) => {
  if (props.open) mode.value = val === 'register' ? 'register' : 'login'
})

onUnmounted(() => {
  clearCountdown()
})

async function handleSendCode() {
  resetFormMessages()
  const trimmedEmail = email.value.trim()
  if (!trimmedEmail) {
    error.value = '请先填写邮箱'
    return
  }

  sendingCode.value = true
  try {
    await sendCode(trimmedEmail, codePurpose.value)
    successMsg.value = '验证码已发送，请查收邮件'
    startCountdown(60)
  } catch (err) {
    error.value = err.message || '发送失败'
  } finally {
    sendingCode.value = false
  }
}

async function handleSubmit() {
  resetFormMessages()
  submitting.value = true
  const trimmedEmail = email.value.trim()

  try {
    if (mode.value === 'register') {
      await register(trimmedEmail, password.value, code.value.trim())
      emit('success')
      emit('close')
    } else if (mode.value === 'login') {
      if (loginMethod.value === 'code') {
        await login(trimmedEmail, { code: code.value.trim() })
      } else {
        await login(trimmedEmail, { password: password.value })
      }
      emit('success')
      emit('close')
    } else if (mode.value === 'forgot') {
      if (password.value !== confirmPassword.value) {
        error.value = '两次输入的密码不一致'
        return
      }
      await resetPassword(trimmedEmail, code.value.trim(), password.value)
      successMsg.value = '密码已重置，请使用新密码登录'
      switchMode('login')
    }
  } catch (err) {
    error.value = err.message || '操作失败'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
