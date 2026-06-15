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
                {{ mode === 'login' ? '登录 OmniVid' : '注册账号' }}
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
            <div class="flex gap-1 p-1 bg-surface-muted rounded-lg">
              <button
                type="button"
                class="flex-1 py-2 text-sm font-medium rounded-md transition-colors cursor-pointer"
                :class="mode === 'login' ? 'bg-bg-card text-primary shadow-sm' : 'text-text-secondary'"
                @click="mode = 'login'"
              >
                登录
              </button>
              <button
                type="button"
                class="flex-1 py-2 text-sm font-medium rounded-md transition-colors cursor-pointer"
                :class="mode === 'register' ? 'bg-bg-card text-primary shadow-sm' : 'text-text-secondary'"
                @click="mode = 'register'"
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
            <div>
              <label class="block text-sm font-medium text-text-secondary mb-1.5">密码</label>
              <input
                v-model="password"
                type="password"
                required
                minlength="6"
                :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
                placeholder="至少 6 位"
                class="w-full h-11 px-4 rounded-lg border border-border bg-bg-page text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>

            <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

            <button
              type="submit"
              class="w-full h-11 rounded-lg bg-primary text-white font-semibold text-sm hover:bg-primary-dark transition-colors cursor-pointer disabled:opacity-60"
              :disabled="submitting"
            >
              {{ submitting ? '处理中...' : (mode === 'login' ? '登录' : '注册') }}
            </button>
          </form>

          <p class="px-6 pb-6 text-xs text-text-muted text-center">
            登录后可使用 AI 视频分析，每个账号每日免费 10 次
          </p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useAuth } from '../composables/useAuth.js'

const props = defineProps({
  open: Boolean,
  initialMode: { type: String, default: 'login' },
})

const emit = defineEmits(['close', 'success'])

const { login, register } = useAuth()
const mode = ref(props.initialMode)
const email = ref('')
const password = ref('')
const error = ref('')
const submitting = ref(false)

watch(() => props.open, (val) => {
  if (val) {
    mode.value = props.initialMode
    error.value = ''
  }
})

watch(() => props.initialMode, (val) => {
  if (props.open) mode.value = val
})

async function handleSubmit() {
  error.value = ''
  submitting.value = true
  try {
    if (mode.value === 'login') {
      await login(email.value.trim(), password.value)
    } else {
      await register(email.value.trim(), password.value)
    }
    emit('success')
    emit('close')
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
