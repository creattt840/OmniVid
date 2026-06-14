<template>
  <section
    class="relative transition-all"
    :class="compact ? 'pt-8 pb-6' : 'pt-12 pb-10 sm:pt-20 sm:pb-16'"
  >
    <div class="relative page-container">
      <div class="max-w-xl sm:max-w-2xl mx-auto text-center">
        <template v-if="showSlogan">
          <h1
            class="font-bold text-text-primary leading-tight mb-3"
            :class="compact ? 'text-2xl sm:text-3xl' : 'text-3xl sm:text-4xl lg:text-5xl'"
          >
            智能视频助理，<span class="text-primary whitespace-nowrap">一键保存</span>
          </h1>
          <p
            class="text-text-secondary leading-relaxed mx-auto"
            :class="compact ? 'text-sm mb-5' : 'text-base sm:text-lg mb-8'"
          >
            粘贴视频链接，智能解析下载。支持 YouTube、Bilibili、抖音、TikTok 等 1800+ 平台
          </p>
        </template>

        <!-- 参考 BibiGPT：居中紧凑输入条 + 右侧操作按钮 -->
        <form @submit.prevent="onSubmit" role="search" aria-label="视频链接解析">
          <div
            class="flex items-center gap-2 p-1.5 pl-4 bg-bg-card rounded-2xl border border-border shadow-sm hover:shadow-md focus-within:shadow-md focus-within:border-primary/40 transition-all"
          >
            <svg class="w-5 h-5 text-text-muted flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            <label for="video-url-input" class="sr-only">粘贴视频链接</label>
            <input
              id="video-url-input"
              v-model="url"
              type="url"
              :placeholder="placeholder"
              class="flex-1 min-w-0 h-11 bg-transparent text-sm sm:text-base text-text-primary placeholder:text-text-muted focus:outline-none"
              :disabled="loading"
              autocomplete="url"
            />
            <button
              type="submit"
              :disabled="loading || !url.trim()"
              class="flex-shrink-0 inline-flex items-center gap-1 h-11 px-4 sm:px-5 rounded-xl bg-primary hover:bg-primary-dark text-white font-medium text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              <svg v-if="loading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <span>{{ loading ? '解析中' : '解析' }}</span>
              <span v-if="!loading" class="hidden sm:inline">→</span>
            </button>
          </div>
        </form>

        <div v-if="showSlogan" class="flex flex-wrap items-center justify-center gap-2 mt-5 text-xs text-text-muted">
          <span>试试：</span>
          <button
            v-for="demo in demos"
            :key="demo.label"
            @click="url = demo.url"
            class="px-3 py-1 rounded-full bg-bg-card border border-border-light hover:border-primary/30 hover:text-primary transition-colors cursor-pointer"
          >
            {{ demo.label }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  loading: Boolean,
  compact: Boolean,
  showSlogan: { type: Boolean, default: true },
})

const emit = defineEmits(['parse'])

const url = ref('')
const placeholder = '粘贴 B站 / YouTube / 抖音等链接，立即解析'

const demos = [
  { label: 'YouTube', url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' },
  { label: 'Bilibili', url: 'https://www.bilibili.com/video/BV1GJ411x7h7' },
]

function onSubmit() {
  const trimmed = url.value.trim()
  if (trimmed && !props.loading) {
    emit('parse', trimmed)
  }
}

defineExpose({
  setUrl(val) { url.value = val },
})
</script>
