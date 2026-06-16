<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="open"
        class="fixed inset-0 z-[300] flex items-center justify-center p-4 bg-black/40"
        @click.self="$emit('close')"
      >
        <div
          class="w-full max-w-sm bg-bg-card rounded-2xl shadow-2xl border border-border overflow-hidden"
          role="alertdialog"
          :aria-labelledby="titleId"
          :aria-describedby="messageId"
        >
          <div class="px-6 pt-6 pb-4">
            <div class="flex items-start gap-3">
              <div class="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div class="min-w-0">
                <h2 :id="titleId" class="text-lg font-bold text-text-primary">{{ title }}</h2>
                <p :id="messageId" class="mt-2 text-sm text-text-secondary leading-relaxed">{{ message }}</p>
              </div>
            </div>
          </div>
          <div class="px-6 pb-6 flex justify-end">
            <button
              type="button"
              class="px-5 py-2.5 rounded-lg text-sm font-medium text-white bg-primary hover:bg-primary-dark transition-colors cursor-pointer"
              @click="$emit('close')"
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
import { useId } from 'vue'

defineProps({
  open: Boolean,
  title: { type: String, default: '提示' },
  message: { type: String, default: '' },
  confirmText: { type: String, default: '我知道了' },
})

defineEmits(['close'])

const titleId = useId()
const messageId = useId()
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
