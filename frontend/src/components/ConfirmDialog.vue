<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="open"
        class="fixed inset-0 z-[300] flex items-center justify-center p-4 bg-black/40"
        @click.self="$emit('cancel')"
      >
        <div class="w-full max-w-sm bg-bg-card rounded-2xl shadow-2xl border border-border overflow-hidden">
          <div class="px-6 pt-6 pb-4">
            <h2 class="text-lg font-bold text-text-primary">{{ title }}</h2>
            <p class="mt-2 text-sm text-text-secondary leading-relaxed">{{ message }}</p>
          </div>
          <div class="px-6 pb-6 flex gap-3 justify-end">
            <button
              type="button"
              class="px-4 py-2 rounded-lg text-sm font-medium text-text-secondary hover:bg-surface-muted transition-colors cursor-pointer"
              @click="$emit('cancel')"
            >
              {{ cancelText }}
            </button>
            <button
              type="button"
              class="px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors cursor-pointer"
              :class="danger ? 'bg-red-500 hover:bg-red-600' : 'bg-primary hover:bg-primary-dark'"
              @click="$emit('confirm')"
            >
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  open: Boolean,
  title: { type: String, default: '确认操作' },
  message: { type: String, default: '' },
  confirmText: { type: String, default: '确定' },
  cancelText: { type: String, default: '取消' },
  danger: { type: Boolean, default: false },
})

defineEmits(['confirm', 'cancel'])
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
