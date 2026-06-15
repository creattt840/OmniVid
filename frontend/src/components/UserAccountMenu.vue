<template>
  <div v-if="isLoggedIn" ref="rootRef" class="relative ml-1">
    <button
      type="button"
      class="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-surface-muted transition-colors cursor-pointer"
      aria-haspopup="true"
      :aria-expanded="open"
      @click.stop="toggle"
    >
      <span
        v-if="isVip"
        class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-700"
      >
        VIP
      </span>
      <span class="text-sm text-text-secondary max-w-[160px] truncate hidden sm:inline">
        {{ userEmail }}
      </span>
      <span class="text-sm text-text-secondary sm:hidden">账号</span>
      <svg
        class="w-4 h-4 text-text-muted transition-transform"
        :class="{ 'rotate-180': open }"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <Transition name="popover">
      <div
        v-if="open"
        class="absolute right-0 top-full mt-2 w-64 bg-bg-card border border-border rounded-xl shadow-lg overflow-hidden z-[100]"
      >
        <div class="px-4 py-3 border-b border-border-light">
          <p class="text-sm font-medium text-text-primary truncate">{{ userEmail }}</p>
          <p v-if="isVip" class="text-xs text-amber-600 mt-1">
            VIP 会员 · 到期 {{ formatDate(vipExpiresAt) }}
          </p>
          <p v-else class="text-xs text-text-muted mt-1">
            免费版 · 今日 AI {{ aiUsageToday }}/{{ aiDailyLimit }}
          </p>
        </div>
        <div class="py-1">
          <button
            type="button"
            class="w-full text-left px-4 py-2.5 text-sm text-text-secondary hover:bg-surface-muted hover:text-primary transition-colors cursor-pointer"
            @click="handleRenew"
          >
            {{ isVip ? '续费 VIP' : '开通 VIP' }}
          </button>
          <button
            type="button"
            class="w-full text-left px-4 py-2.5 text-sm text-text-muted hover:bg-surface-muted hover:text-text-primary transition-colors cursor-pointer"
            @click="handleLogout"
          >
            退出登录
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'

defineProps({
  isLoggedIn: { type: Boolean, default: false },
  isVip: { type: Boolean, default: false },
  userEmail: { type: String, default: '' },
  vipExpiresAt: { type: String, default: '' },
  aiUsageToday: { type: Number, default: 0 },
  aiDailyLimit: { type: Number, default: 3 },
})

const emit = defineEmits(['renew-vip', 'logout'])

const open = ref(false)
const rootRef = ref(null)

function toggle() {
  open.value = !open.value
}

function close() {
  open.value = false
}

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

function handleRenew() {
  close()
  emit('renew-vip')
}

function handleLogout() {
  close()
  emit('logout')
}

function onClickOutside(e) {
  if (rootRef.value && !rootRef.value.contains(e.target)) {
    close()
  }
}

watch(open, (isOpen) => {
  if (isOpen) {
    // 延迟绑定，避免打开弹窗的同一击立即触发关闭
    setTimeout(() => document.addEventListener('click', onClickOutside), 0)
  } else {
    document.removeEventListener('click', onClickOutside)
  }
})

onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>

<style scoped>
.popover-enter-active,
.popover-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.popover-enter-from,
.popover-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
