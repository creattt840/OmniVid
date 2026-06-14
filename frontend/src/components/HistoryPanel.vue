<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="open"
        class="fixed inset-0 z-[150] flex justify-end"
        @click.self="$emit('close')"
      >
        <div class="absolute inset-0 bg-black/30 backdrop-blur-sm" />
        <aside class="relative w-full max-w-sm bg-bg-card h-full shadow-2xl flex flex-col animate-slide-in">
          <div class="flex items-center justify-between px-5 py-4 border-b border-border-light">
            <h2 class="font-bold text-text-primary">分析历史</h2>
            <div class="flex items-center gap-2">
              <button
                v-if="items.length"
                type="button"
                class="text-xs text-text-muted hover:text-red-500 transition-colors cursor-pointer"
                @click="handleClear"
              >
                清空
              </button>
              <button
                type="button"
                class="p-2 rounded-xl hover:bg-gray-100 text-text-muted cursor-pointer"
                aria-label="关闭"
                @click="$emit('close')"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <div class="flex-1 overflow-y-auto p-4 space-y-3">
            <p v-if="!items.length" class="text-sm text-text-muted text-center py-12">
              暂无历史记录<br><span class="text-xs">分析完成后自动保存</span>
            </p>
            <button
              v-for="item in items"
              :key="item.id"
              type="button"
              class="w-full flex gap-3 p-3 rounded-2xl border border-border-light hover:border-primary/30 hover:bg-primary-light/30 text-left transition-all cursor-pointer group"
              @click="$emit('select', item.url)"
            >
              <div class="w-16 h-10 rounded-lg bg-gray-100 flex-shrink-0 overflow-hidden">
                <img
                  v-if="item.thumbnail"
                  :src="thumbnailProxy(item.thumbnail)"
                  :alt="item.title"
                  class="w-full h-full object-cover"
                />
              </div>
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium text-text-primary line-clamp-2 group-hover:text-primary transition-colors">
                  {{ item.title }}
                </p>
                <p class="text-xs text-text-muted mt-1">
                  {{ item.platform }} · {{ formatDate(item.analyzedAt) }}
                </p>
              </div>
              <button
                type="button"
                class="flex-shrink-0 p-1 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-50 text-text-muted hover:text-red-500 transition-all cursor-pointer"
                aria-label="删除"
                @click.stop="$emit('remove', item.id)"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </button>
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  open: Boolean,
  items: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'select', 'remove', 'clear'])

function thumbnailProxy(url) {
  return '/api/proxy/thumbnail?url=' + encodeURIComponent(url)
}

function formatDate(ts) {
  return new Date(ts).toLocaleString('zh-CN', {
    month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

function handleClear() {
  if (confirm('确定清空所有分析历史？')) {
    emit('clear')
  }
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
@keyframes slide-in { from { transform: translateX(100%); } to { transform: translateX(0); } }
.animate-slide-in { animation: slide-in 0.25s ease; }
</style>
