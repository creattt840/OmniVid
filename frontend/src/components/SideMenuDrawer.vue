<template>
  <Teleport to="body">
    <Transition name="overlay-fade">
      <div
        v-if="open"
        class="fixed inset-0 z-[150] flex justify-start"
        @click.self="emit('close')"
      >
        <div class="overlay-backdrop" />
        <aside
          class="relative w-full max-w-xs bg-bg-card h-full shadow-2xl flex flex-col animate-slide-in-left"
          role="dialog"
          aria-label="导航菜单"
        >
          <!-- 头部 -->
          <div class="flex items-center justify-between px-5 py-4 border-b border-border-light">
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg bg-primary flex items-center justify-center">
                <svg class="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              </div>
              <span class="font-bold text-text-primary">OmniVid</span>
            </div>
            <button
              type="button"
              class="p-2 rounded-lg hover:bg-surface-muted text-text-muted cursor-pointer"
              aria-label="关闭菜单"
              @click="emit('close')"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- 菜单内容 -->
          <nav class="flex-1 overflow-y-auto px-4 py-4">
            <!-- 工具区 -->
            <p class="px-3 mb-2 text-xs font-semibold text-text-muted uppercase tracking-wide">工具</p>
            <ul class="space-y-1 mb-6">
              <li v-for="item in toolItems" :key="item.id">
                <button
                  type="button"
                  class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-text-secondary hover:bg-surface-muted hover:text-primary transition-colors cursor-pointer"
                  @click="handleToolClick(item)"
                >
                  <span class="w-5 h-5 flex-shrink-0 text-text-muted" v-html="iconSvg(item.icon)" />
                  <span class="flex-1 text-left">{{ item.label }}</span>
                  <span
                    v-if="item.badge === 'count' && historyCount > 0"
                    class="px-1.5 py-0.5 text-[10px] font-bold bg-primary text-white rounded-full"
                  >
                    {{ historyCount > 9 ? '9+' : historyCount }}
                  </span>
                  <span
                    v-else-if="item.badge === 'soon'"
                    class="px-1.5 py-0.5 text-[10px] font-medium bg-surface-muted text-text-muted rounded-full"
                  >
                    即将上线
                  </span>
                </button>
              </li>
            </ul>

            <!-- 了解区 -->
            <p class="px-3 mb-2 text-xs font-semibold text-text-muted uppercase tracking-wide">了解 OmniVid</p>
            <ul class="space-y-1">
              <li v-for="item in learnItems" :key="item.href">
                <button
                  type="button"
                  class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-text-secondary hover:bg-surface-muted hover:text-primary transition-colors cursor-pointer"
                  @click="handleNavigate(item.href)"
                >
                  <svg class="w-5 h-5 flex-shrink-0 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                  <span>{{ item.label }}</span>
                </button>
              </li>
            </ul>
          </nav>

          <!-- 底部 -->
          <div class="px-5 py-3 border-t border-border-light text-xs text-text-muted text-center">
            OmniVid v1.0 · 仅供个人学习使用
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  open: Boolean,
  historyCount: { type: Number, default: 0 },
})

const emit = defineEmits(['close', 'new-parse', 'history', 'upload-local', 'navigate'])

const toolItems = [
  { id: 'new-parse', label: '新建解析', icon: 'plus' },
  { id: 'history', label: '分析历史', icon: 'clock', badge: 'count' },
  { id: 'upload-local', label: '本地视频上传', icon: 'upload' },
  { id: 'help', label: '使用帮助', icon: 'help', href: '#howto' },
]

const learnItems = [
  { label: '支持平台', href: '#platforms' },
  { label: '功能亮点', href: '#features' },
  { label: 'VIP 套餐', href: '#pricing' },
]

const ICONS = {
  plus: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>',
  clock: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
  upload: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>',
  help: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
}

function iconSvg(name) {
  return ICONS[name] || ''
}

function handleToolClick(item) {
  if (item.id === 'new-parse') {
    emit('new-parse')
  } else if (item.id === 'history') {
    emit('history')
  } else if (item.id === 'upload-local') {
    emit('upload-local')
  } else if (item.href) {
    emit('navigate', item.href)
  }
  emit('close')
}

function handleNavigate(href) {
  emit('navigate', href)
  emit('close')
}

function onKeydown(e) {
  if (e.key === 'Escape' && props.open) emit('close')
}

watch(() => props.open, (isOpen) => {
  document.body.style.overflow = isOpen ? 'hidden' : ''
})

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>

<style scoped>
@keyframes slide-in-left { from { transform: translateX(-100%); } to { transform: translateX(0); } }
.animate-slide-in-left { animation: slide-in-left 0.25s ease; }
</style>
