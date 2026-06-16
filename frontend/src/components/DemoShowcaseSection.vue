<template>
  <section class="-mt-2 pb-10 sm:pb-12" aria-label="AI 分析成果演示">
    <div class="page-container">
      <div class="workspace-card animate-fade-up">
        <div class="grid grid-cols-1 lg:grid-cols-5 items-start gap-5 lg:gap-0 divide-y lg:divide-y-0 lg:divide-x divide-border-light">
          <!-- 左栏：视频预览 + 切换 -->
          <div class="lg:col-span-2 px-4 sm:px-5 lg:px-6 pt-4 sm:pt-5 lg:pt-6 pb-4 sm:pb-5 lg:pb-6">
            <div class="relative aspect-video bg-gray-100 rounded-lg overflow-hidden">
              <img
                v-if="thumbnailUrl"
                :src="thumbnailUrl"
                :alt="activeDemo.title"
                class="w-full h-full object-cover"
                @error="(e) => e.target.style.display = 'none'"
              />
              <div v-else class="w-full h-full flex items-center justify-center text-text-muted">
                <svg class="w-16 h-16 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                    d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
              <div
                v-if="activeDemo.duration_string"
                class="absolute bottom-3 right-3 px-2.5 py-1 bg-black/70 text-white text-xs rounded-lg font-medium pointer-events-none"
              >
                {{ activeDemo.duration_string }}
              </div>
              <div class="absolute top-3 left-3 pointer-events-none">
                <span class="inline-flex items-center gap-1 px-3 py-1 bg-white/90 backdrop-blur-sm text-primary text-xs font-medium rounded-full">
                  {{ activeDemo.platform }}
                </span>
              </div>
              <a
                :href="activeDemo.url"
                target="_blank"
                rel="noopener noreferrer"
                class="absolute inset-0 flex items-center justify-center bg-black/0 hover:bg-black/10 transition-colors group"
                :aria-label="`在 ${platformKind} 打开原视频`"
              >
                <span class="w-14 h-14 rounded-full bg-white/90 shadow-lg flex items-center justify-center opacity-80 group-hover:opacity-100 group-hover:scale-105 transition-all">
                  <svg class="w-7 h-7 text-primary ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </span>
              </a>
            </div>

            <h3 class="font-bold text-text-primary text-base sm:text-lg leading-snug mt-4 mb-3 line-clamp-2">
              {{ activeDemo.title }}
            </h3>

            <!-- 切换演示视频 -->
            <div class="border border-border-light rounded-xl overflow-hidden">
              <button
                type="button"
                class="w-full flex items-center justify-between gap-2 px-3 py-2.5 text-sm font-medium text-text-primary hover:bg-surface-muted/80 transition-colors cursor-pointer"
                @click="switcherOpen = !switcherOpen"
              >
                <span>切换演示视频</span>
                <svg
                  class="w-4 h-4 text-text-muted transition-transform"
                  :class="switcherOpen ? 'rotate-180' : ''"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div v-show="switcherOpen" class="px-2 pb-2 space-y-1.5 border-t border-border-light">
                <button
                  v-for="item in demos"
                  :key="item.id"
                  type="button"
                  class="w-full flex items-start gap-3 p-2.5 rounded-lg text-left transition-colors cursor-pointer"
                  :class="item.id === activeId
                    ? 'bg-primary text-white shadow-sm'
                    : 'bg-bg-card border border-border-light hover:border-primary/25 hover:bg-primary-light/30'"
                  @click="selectDemo(item.id)"
                >
                  <img
                    :src="item.icon"
                    :alt="item.platformKind"
                    class="w-9 h-9 flex-shrink-0 object-contain rounded-md"
                    :class="item.id === activeId ? 'bg-white/15 p-1' : ''"
                  />
                  <div class="min-w-0 flex-1">
                    <p
                      class="text-sm font-medium leading-snug line-clamp-2"
                      :class="item.id === activeId ? 'text-white' : 'text-text-primary'"
                    >
                      {{ item.label }}
                    </p>
                    <p
                      class="text-xs mt-0.5 leading-relaxed line-clamp-2"
                      :class="item.id === activeId ? 'text-white/80' : 'text-text-muted'"
                    >
                      {{ item.description }}
                    </p>
                  </div>
                </button>
              </div>
            </div>
          </div>

          <!-- 右栏：AI 分析 -->
          <div class="lg:col-span-3 flex flex-col overflow-hidden max-h-[min(75vh,800px)] px-4 sm:px-5 lg:px-6 pt-2 sm:pt-3 pb-4 sm:pb-5 lg:pb-6 lg:pl-5">
            <VideoSummary
              :key="activeId"
              embedded
              demo-mode
              :url="activeDemo.url"
              :video-url="activeDemo.url"
              :thumbnail="activeDemo.thumbnail"
              :initial-history="showcaseHistory"
            />
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import VideoSummary from './VideoSummary.vue'
import showcaseStore from '../data/demo-showcases.json'
import legacyDemo from '../data/demo-showcase.json'

const switcherOpen = ref(true)

function isYoutube(url) {
  return /youtube\.com|youtu\.be/i.test(url || '')
}

function isBilibili(url) {
  return /bilibili\.com|b23\.tv/i.test(url || '')
}

function normalizeDemo(raw) {
  const url = raw.url || ''
  const platformKind = isYoutube(url) ? 'YouTube' : isBilibili(url) ? 'B站' : raw.platform || '视频'
  const icon = isYoutube(url)
    ? '/logos/youtube.svg'
    : isBilibili(url)
      ? '/logos/bilibili.svg'
      : '/logos/youtube.svg'
  const title = raw.title || ''
  const label = raw.label || `${platformKind}：${title.length > 28 ? title.slice(0, 28) + '…' : title}`
  const description = raw.description || (raw.summary?.summary?.slice(0, 80) + (raw.summary?.summary?.length > 80 ? '…' : '')) || ''

  return {
    ...raw,
    label,
    description,
    platformKind,
    icon,
  }
}

const demos = computed(() => {
  const list = showcaseStore.demos?.length
    ? showcaseStore.demos
    : [legacyDemo]
  return list.map(normalizeDemo)
})

const activeId = ref(demos.value[0]?.id || 'default')

const activeDemo = computed(() =>
  demos.value.find(d => d.id === activeId.value) || demos.value[0]
)

const platformKind = computed(() => activeDemo.value?.platformKind || '视频')

const thumbnailUrl = computed(() => {
  const thumb = activeDemo.value?.thumbnail
  if (!thumb) return ''
  return '/api/proxy/thumbnail?url=' + encodeURIComponent(thumb)
})

const showcaseHistory = computed(() => {
  const d = activeDemo.value
  if (!d) return {}
  return {
    title: d.title,
    platform: d.platform,
    transcriptSource: d.transcriptSource || 'subtitle',
    summary: d.summary || {},
    mindmap: d.mindmap || '',
    segments: d.segments || [],
    article: d.article || '',
    chatHistory: [],
  }
})

function selectDemo(id) {
  if (id === activeId.value) return
  activeId.value = id
}
</script>
