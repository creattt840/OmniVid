<template>
  <section
    class="relative transition-all"
    :class="compact ? 'pt-8 pb-6' : 'pt-12 pb-10 sm:pt-20 sm:pb-16'"
  >
    <div class="relative max-w-3xl mx-auto px-4 sm:px-6 text-center">
      <template v-if="showSlogan">
        <h1
          class="font-bold text-text-primary leading-tight mb-3"
          :class="compact ? 'text-2xl sm:text-3xl' : 'text-3xl sm:text-5xl'"
        >
          万能视频下载，
          <span class="text-primary">一键保存</span>
        </h1>
        <p
          class="text-text-secondary leading-relaxed max-w-xl mx-auto"
          :class="compact ? 'text-sm mb-5' : 'text-base sm:text-lg mb-8'"
        >
          粘贴视频链接，智能解析下载。支持 YouTube、Bilibili、抖音、TikTok 等 1800+ 平台
        </p>
      </template>

      <!-- painting 风格胶囊搜索条 -->
      <div class="max-w-2xl mx-auto">
        <form @submit.prevent="onSubmit" role="search" aria-label="视频链接解析">
          <div class="relative flex items-center bg-bg-card rounded-full border border-border shadow-sm hover:shadow-md focus-within:shadow-md focus-within:border-primary/40 transition-all">
            <svg class="absolute left-5 w-5 h-5 text-text-muted pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <label for="video-url-input" class="sr-only">粘贴视频链接</label>
            <input
              id="video-url-input"
              v-model="url"
              type="url"
              :placeholder="placeholder"
              class="flex-1 h-12 sm:h-14 pl-13 pr-4 sm:pr-36 bg-transparent text-base text-text-primary placeholder:text-text-muted focus:outline-none rounded-full"
              :disabled="loading"
              autocomplete="url"
            />
            <!-- 桌面端内嵌按钮 -->
            <button
              type="submit"
              :disabled="loading || !url.trim()"
              class="hidden sm:flex absolute right-1.5 items-center gap-1.5 h-11 px-6 rounded-full bg-primary hover:bg-primary-dark text-white font-medium text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              <svg v-if="loading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              {{ loading ? '解析中...' : '解析' }}
            </button>
            <!-- 移动端圆形按钮 -->
            <button
              type="submit"
              :disabled="loading || !url.trim()"
              class="sm:hidden absolute right-2 w-9 h-9 flex items-center justify-center rounded-full bg-primary text-white disabled:opacity-50 cursor-pointer"
            >
              <svg v-if="loading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
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
const placeholder = '粘贴视频链接，支持 YouTube / Bilibili / 抖音 / TikTok ...'

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

<style scoped>
.pl-13 { padding-left: 3.25rem; }
</style>
