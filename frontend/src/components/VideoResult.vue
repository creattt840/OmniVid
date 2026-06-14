<template>
  <div class="animate-fade-up bg-bg-card rounded-3xl border border-border-light shadow-sm overflow-hidden">
    <!-- 缩略图区域 -->
    <div class="relative aspect-video bg-gray-100">
      <img
        v-if="video.thumbnail"
        :src="thumbnailUrl"
        :alt="video.title"
        class="w-full h-full object-cover"
        @error="(e) => e.target.style.display = 'none'"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-text-muted">
        <svg class="w-16 h-16 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      </div>
      <div v-if="video.duration_string" class="absolute bottom-3 right-3 px-2.5 py-1 bg-black/70 text-white text-xs rounded-lg font-medium">
        {{ video.duration_string }}
      </div>
      <div class="absolute top-3 left-3">
        <span class="inline-flex items-center gap-1 px-3 py-1 bg-white/90 backdrop-blur-sm text-primary text-xs font-medium rounded-full">
          {{ video.platform }}
        </span>
      </div>
    </div>

    <!-- 视频信息 -->
    <div class="p-5 sm:p-6">
      <h3 class="text-lg sm:text-xl font-bold text-text-primary leading-snug mb-3 line-clamp-2">
        {{ video.title }}
      </h3>

      <!-- hashtag 标签（painting 风格） -->
      <div class="flex flex-wrap gap-2 mb-4">
        <span class="text-xs text-text-muted"># {{ video.platform }}</span>
        <span v-if="bestHeight" class="text-xs text-text-muted"># {{ bestHeight }}p</span>
        <span v-if="hasNoWatermark" class="text-xs text-text-muted"># 无水印</span>
        <span v-if="video.subtitles?.length" class="text-xs text-text-muted"># 含字幕</span>
      </div>

      <div class="flex flex-wrap items-center gap-3 text-sm text-text-secondary mb-5">
        <span class="inline-flex items-center gap-1.5">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          {{ video.uploader }}
        </span>
        <span v-if="video.view_count" class="inline-flex items-center gap-1.5">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          {{ formatViewCount(video.view_count) }}
        </span>
      </div>

      <!-- 格式选择 -->
      <div class="mb-5">
        <h4 class="text-sm font-semibold text-text-primary mb-3">选择清晰度</h4>
        <div class="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto pr-1">
          <button
            v-for="fmt in video.formats"
            :key="fmt.format_id"
            @click="selectedFormat = fmt.format_id"
            :class="[
              'flex items-center gap-3 px-4 py-3 rounded-2xl border text-left transition-all cursor-pointer',
              selectedFormat === fmt.format_id
                ? 'border-primary bg-primary-light ring-1 ring-primary/20'
                : 'border-border-light hover:border-primary/30 hover:bg-gray-50'
            ]"
          >
            <div
              class="flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold"
              :class="selectedFormat === fmt.format_id ? 'bg-primary text-white' : 'bg-gray-100 text-text-muted'"
            >
              {{ fmt.height || '?' }}p
            </div>
            <div class="min-w-0 flex-1">
              <div class="text-sm font-medium text-text-primary truncate">{{ fmt.label }}</div>
              <div class="text-xs text-text-muted">{{ fmt.ext.toUpperCase() }} · {{ fmt.has_audio ? '含音频' : '仅视频' }}</div>
            </div>
          </button>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex flex-col sm:flex-row gap-3">
        <button
          @click="$emit('download', selectedFormat)"
          :disabled="!selectedFormat || downloading"
          class="flex-1 h-13 flex items-center justify-center gap-2 rounded-full bg-primary hover:bg-primary-dark text-white font-semibold text-base transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg cursor-pointer"
        >
          <svg v-if="downloading" class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          {{ downloading ? '下载中，请稍候...' : '立即下载' }}
        </button>

        <button
          @click="$emit('analyze')"
          :disabled="analyzing"
          class="flex-1 h-13 flex items-center justify-center gap-2 rounded-full border-2 border-primary text-primary hover:bg-primary-light font-semibold text-base transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          <svg v-if="analyzing" class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span v-else>🤖</span>
          {{ analyzing ? '分析中...' : 'AI 分析' }}
        </button>
      </div>

      <p v-if="errorMsg" class="mt-3 text-sm text-red-500 text-center">{{ errorMsg }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  video: { type: Object, required: true },
  downloading: Boolean,
  analyzing: Boolean,
  errorMsg: String,
})

defineEmits(['download', 'analyze'])

const thumbnailUrl = computed(() => {
  if (!props.video.thumbnail) return ''
  return '/api/proxy/thumbnail?url=' + encodeURIComponent(props.video.thumbnail)
})

const selectedFormat = ref(
  props.video.formats?.length > 0 ? props.video.formats[0].format_id : ''
)

const bestHeight = computed(() => {
  const heights = props.video.formats?.map(f => f.height).filter(Boolean) || []
  return heights.length ? Math.max(...heights) : null
})

const hasNoWatermark = computed(() =>
  props.video.platform === '抖音' || props.video.formats?.some(f => f.format_id === 'douyin_nowm')
)

function formatViewCount(count) {
  if (!count) return ''
  if (count >= 100000000) return (count / 100000000).toFixed(1) + '亿'
  if (count >= 10000) return (count / 10000).toFixed(1) + '万'
  return count.toLocaleString()
}
</script>

<style scoped>
.h-13 { height: 3.25rem; }
</style>
