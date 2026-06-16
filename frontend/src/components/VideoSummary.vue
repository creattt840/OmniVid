<template>
  <div
    :class="embedded
      ? 'flex flex-col h-full max-h-full min-h-0 overflow-hidden'
      : 'bg-bg-card rounded-3xl border border-border-light shadow-sm overflow-hidden animate-fade-up mt-6'"
  >
    <!-- 头部 -->
    <div
      class="flex-shrink-0 border-b border-border-light flex items-center justify-between gap-3"
      :class="embedded ? 'px-1 py-2' : 'px-5 sm:px-6 py-4'"
    >
      <div class="flex items-center gap-2.5 min-w-0">
        <div class="w-9 h-9 rounded-lg bg-primary-light flex items-center justify-center flex-shrink-0">
          <svg class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <div class="min-w-0">
          <h3 class="font-bold text-text-primary truncate">AI 分析</h3>
          <p v-if="!embedded" class="text-xs text-text-muted truncate">
            {{ meta.title }}
            <span v-if="meta.transcript_source" class="ml-1">
              · {{ meta.transcript_source === 'subtitle' ? '字幕提取' : '语音转写' }}
            </span>
          </p>
          <p v-else-if="meta.transcript_source" class="text-xs text-text-muted truncate">
            {{ meta.transcript_source === 'subtitle' ? '字幕提取' : '语音转写' }}
            <span v-if="demoMode" class="ml-1.5 text-primary/80">· 演示数据</span>
          </p>
        </div>
      </div>
      <button
        v-if="!embedded"
        @click="$emit('close')"
        class="flex-shrink-0 p-2 rounded-lg hover:bg-surface-muted text-text-muted transition-colors cursor-pointer"
        aria-label="关闭"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- 状态栏 -->
    <div
      v-if="(phase !== 'ready' && phase !== 'error') || rewriteLoading"
      class="flex-shrink-0 bg-primary-light/50 border-b border-border-light"
      :class="embedded ? 'px-1 py-2' : 'px-5 sm:px-6 py-3'"
    >
      <div class="flex items-center gap-2 text-sm text-primary">
        <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span>{{ statusText }}</span>
      </div>
    </div>

    <!-- 错误 -->
    <div v-if="error" class="flex-shrink-0 px-5 sm:px-6 py-4 bg-red-50 text-red-700 text-sm flex items-center justify-between gap-3">
      <span>{{ error }}</span>
      <button
        v-if="authRetryPending && !isLoggedIn"
        type="button"
        class="flex-shrink-0 px-3 py-1.5 rounded-lg bg-primary text-white text-xs font-medium hover:bg-primary-dark cursor-pointer"
        @click="emit('upgrade-required', 'AUTH_REQUIRED')"
      >
        去登录
      </button>
    </div>

    <!-- Tabs -->
    <div
      class="flex-shrink-0 flex items-center gap-1 border-b border-border-light overflow-x-auto"
      :class="embedded ? 'px-0 py-1' : 'px-3 sm:px-4 py-2'"
    >
      <button
        v-for="tab in visibleTabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        :class="[
          'flex-shrink-0 px-3 sm:px-4 py-2 text-sm font-medium transition-colors cursor-pointer rounded-lg',
          activeTab === tab.id
            ? 'bg-primary-light text-primary'
            : 'text-text-muted hover:text-text-primary hover:bg-surface-muted'
        ]"
      >
        {{ tab.label }}
      </button>
      <!-- 导出按钮 -->
      <div v-if="phase === 'ready' && summary.summary && !demoMode" class="ml-auto flex items-center gap-1 px-3 flex-shrink-0">
        <button
          type="button"
          class="px-2.5 py-1 rounded-lg text-xs font-medium text-text-muted hover:text-primary hover:bg-primary-light transition-colors cursor-pointer"
          title="导出 Markdown"
          @click="exportMarkdown"
        >
          MD
        </button>
        <button
          type="button"
          class="px-2.5 py-1 rounded-lg text-xs font-medium text-text-muted hover:text-primary hover:bg-primary-light transition-colors cursor-pointer"
          title="导出 PDF"
          @click="exportPdf"
        >
          PDF
        </button>
      </div>
    </div>

    <!-- Tab 内容（固定高度区域内滚动） -->
    <div
      class="flex-1 min-h-0 overflow-y-auto"
      :class="embedded ? 'p-3 sm:p-4' : 'p-5 sm:p-6 min-h-[280px] max-h-[520px]'"
    >
      <!-- 摘要 -->
      <div v-show="activeTab === 'summary'" class="flex gap-4">
        <div class="flex-1 min-w-0 space-y-5">
        <!-- 流式生成中：摘要正文 -->
        <section v-if="phase === 'summarizing' && streamingSummary">
          <h4 class="text-sm font-semibold text-text-primary mb-2">摘要</h4>
          <p class="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">
            {{ streamingSummary }}
            <span class="inline-block w-1.5 h-4 bg-primary animate-pulse ml-0.5" />
          </p>
        </section>

        <!-- 生成中：其他区块骨架屏 -->
        <template v-if="phase === 'summarizing'">
          <section v-if="!streamingSummary" class="py-4">
            <div class="h-4 w-16 bg-surface-muted rounded animate-pulse mb-3" />
            <div class="space-y-2">
              <div class="h-3 bg-surface-muted rounded animate-pulse" />
              <div class="h-3 bg-surface-muted rounded animate-pulse w-5/6" />
              <div class="h-3 bg-surface-muted rounded animate-pulse w-4/6" />
            </div>
          </section>
          <section class="py-2">
            <div class="h-4 w-20 bg-surface-muted rounded animate-pulse mb-3" />
            <div class="space-y-2">
              <div v-for="n in 3" :key="n" class="h-3 bg-surface-muted rounded animate-pulse" :class="n === 3 ? 'w-2/3' : ''" />
            </div>
          </section>
        </template>

        <!-- 完成后：结构化展示 -->
        <template v-if="phase === 'ready' || (phase !== 'summarizing' && summary.summary)">
          <section v-if="summary.summary">
            <h4 class="text-sm font-semibold text-text-primary mb-2">摘要</h4>
            <p class="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">{{ summary.summary }}</p>
          </section>

          <section v-if="summary.highlights?.length">
            <h4 class="text-sm font-semibold text-text-primary mb-2">核心要点</h4>
            <ul class="space-y-2">
              <li
                v-for="(item, i) in summary.highlights"
                :key="i"
                class="flex gap-2 text-sm text-text-secondary"
              >
                <span class="text-primary font-bold flex-shrink-0">{{ i + 1 }}.</span>
                <span>{{ item }}</span>
              </li>
            </ul>
          </section>

          <section v-if="summary.chapters?.length">
            <h4 class="text-sm font-semibold text-text-primary mb-2">章节大纲</h4>
            <div class="space-y-3">
              <div
                v-for="(ch, i) in summary.chapters"
                :key="i"
                :id="'chapter-' + i"
                class="p-3 rounded-2xl bg-gray-50 border border-border-light hover:border-primary/30 transition-colors cursor-pointer group"
                @click="jumpToChapter(ch)"
              >
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-xs font-mono text-primary bg-primary-light px-2 py-0.5 rounded-lg">{{ ch.time }}</span>
                  <span class="text-sm font-medium text-text-primary flex-1">{{ ch.title }}</span>
                  <a
                    v-if="videoUrl && !localMode && !demoMode"
                    :href="buildTimestampUrl(ch.time)"
                    target="_blank"
                    rel="noopener"
                    class="opacity-0 group-hover:opacity-100 p-1 rounded-lg hover:bg-primary-light text-primary transition-all"
                    title="在原视频中打开"
                    @click.stop
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                </div>
                <p v-if="ch.summary" class="text-xs text-text-muted leading-relaxed">{{ ch.summary }}</p>
              </div>
            </div>
          </section>

          <section v-if="summary.terms?.length">
            <h4 class="text-sm font-semibold text-text-primary mb-2">术语解释</h4>
            <dl class="space-y-2">
              <div v-for="(t, i) in summary.terms" :key="i" class="text-sm">
                <dt class="font-medium text-text-primary">{{ t.term }}</dt>
                <dd class="text-text-muted mt-0.5">{{ t.definition }}</dd>
              </div>
            </dl>
          </section>
        </template>

        <p v-if="phase === 'ready' && !summary.summary && !streamingSummary" class="text-sm text-text-muted text-center py-8">
          暂无摘要内容
        </p>
        </div>

        <!-- 章节快速导航（桌面端侧边栏） -->
        <nav
          v-if="summary.chapters?.length && (phase === 'ready' || summary.summary)"
          class="hidden xl:block w-36 flex-shrink-0 sticky top-0 self-start"
        >
          <p class="text-xs font-semibold text-text-muted mb-2 uppercase tracking-wide">章节导航</p>
          <ul class="space-y-1">
            <li v-for="(ch, i) in summary.chapters" :key="'nav-' + i">
              <button
                type="button"
                class="w-full text-left px-2 py-1.5 rounded-lg text-xs text-text-secondary hover:bg-primary-light hover:text-primary transition-colors cursor-pointer truncate"
                :title="ch.title"
                @click="jumpToChapter(ch, i)"
              >
                <span class="font-mono text-primary/70">{{ ch.time }}</span>
                {{ ch.title }}
              </button>
            </li>
          </ul>
        </nav>
      </div>

      <!-- 转录 -->
      <div v-show="activeTab === 'transcript'">
        <div v-if="segments.length" class="space-y-2">
          <div class="flex flex-wrap items-center gap-2 pb-2 border-b border-border-light">
            <template v-if="!demoMode">
              <span class="text-xs text-text-muted">导出：</span>
              <button
                v-for="fmt in subtitleFormats"
                :key="fmt.id"
                type="button"
                class="px-3 py-1 rounded-lg text-xs font-medium border border-border-light text-text-secondary hover:border-primary/30 hover:text-primary transition-colors cursor-pointer"
                @click="exportTranscript(fmt.id)"
              >
                {{ fmt.label }}
              </button>
              <template v-if="!localMode">
                <span class="text-xs text-text-muted ml-1">翻译：</span>
                <select
                  v-model="translateLang"
                  class="px-2 py-1 rounded-lg text-xs border border-border-light text-text-secondary focus:outline-none focus:ring-1 focus:ring-primary/30 cursor-pointer"
                >
                  <option v-for="lang in translateLangs" :key="lang.id" :value="lang.id">{{ lang.label }}</option>
                </select>
                <button
                  type="button"
                  class="px-3 py-1 rounded-lg text-xs font-medium border border-primary/30 text-primary hover:bg-primary-light transition-colors cursor-pointer disabled:opacity-50"
                  :disabled="translating"
                  @click="handleTranslateDownload"
                >
                  {{ translating ? '翻译中...' : '翻译下载 SRT' }}
                </button>
              </template>
            </template>
            <span v-else class="text-xs text-text-muted">演示转录文本（只读预览）</span>
          </div>
          <div ref="transcriptContainer" class="space-y-1 font-mono text-xs">
            <div
              v-for="(seg, i) in segments"
              :key="i"
              :ref="el => { if (el) segmentRefs[i] = el }"
              class="flex gap-3 py-1.5 hover:bg-gray-50 rounded-lg px-2 -mx-2 transition-colors"
              :class="highlightSegment === i ? 'bg-primary-light/60 ring-1 ring-primary/20' : ''"
            >
              <span class="text-primary flex-shrink-0 w-14">{{ formatTime(seg.start) }}</span>
              <span class="text-text-secondary leading-relaxed">{{ seg.text }}</span>
            </div>
          </div>
        </div>
        <p v-else class="text-sm text-text-muted text-center py-8">
          {{ phase === 'summarizing' ? '转录文本加载中...' : '暂无转录文本' }}
        </p>
      </div>

      <!-- 思维导图 -->
      <div v-show="activeTab === 'mindmap'">
        <MindMapView
          v-if="mindmap && activeTab === 'mindmap'"
          ref="mindmapRef"
          :key="mindmap.slice(0, 80)"
          :content="mindmap"
          :title="meta.title || '思维导图'"
        />
        <p v-else-if="!mindmap" class="text-sm text-text-muted text-center py-8">
          {{ phase === 'summarizing' ? '思维导图生成中...' : '暂无思维导图' }}
        </p>
      </div>

      <!-- 文章视图 -->
      <div v-show="activeTab === 'article'">
        <div v-if="!articleContent && !articleStreaming && phase === 'ready'" class="text-center py-8">
          <p class="text-sm text-text-muted mb-4">将口语化转录改写为结构清晰的书面文章</p>
          <button
            type="button"
            class="px-5 py-2.5 rounded-full bg-primary text-white text-sm font-medium hover:bg-primary-dark transition-colors cursor-pointer disabled:opacity-50"
            :disabled="rewriteLoading || !canRewrite"
            @click="startRewrite"
          >
            {{ rewriteLoading ? '生成中...' : '生成 AI 改写文章' }}
          </button>
          <p v-if="!canRewrite" class="text-xs text-text-muted mt-3">缺少转录文本，无法生成改写文章</p>
        </div>
        <div v-else class="article-content">
          <div v-html="renderedArticle" />
          <span v-if="articleStreaming" class="inline-block w-1.5 h-4 bg-primary animate-pulse ml-0.5 align-middle" />
        </div>
      </div>

      <!-- AI 问答 -->
      <div v-show="activeTab === 'chat'" class="flex flex-col h-full min-h-[240px]">
        <div ref="chatContainer" class="flex-1 overflow-y-auto space-y-3 mb-4 pr-1">
          <div v-if="!chatMessages.length" class="text-sm text-text-muted text-center py-8">
            基于视频内容提问，例如：「视频的核心观点是什么？」
          </div>
          <div
            v-for="(msg, i) in chatMessages"
            :key="i"
            :class="[
              'rounded-2xl text-sm leading-relaxed',
              msg.role === 'user'
                ? 'max-w-[85%] ml-auto px-4 py-2.5 bg-primary text-white rounded-br-md whitespace-pre-wrap'
                : 'max-w-full px-4 py-3 bg-gray-50 text-text-secondary rounded-bl-md border border-border-light'
            ]"
          >
            <div
              v-if="msg.role === 'assistant'"
              class="article-content chat-md"
              v-html="renderMarkdown(msg.content)"
            />
            <template v-else>{{ msg.content }}</template>
            <span v-if="msg.streaming" class="inline-block w-1.5 h-3.5 bg-current opacity-60 animate-pulse ml-0.5" />
          </div>
        </div>
        <form @submit.prevent="sendChat" class="flex gap-2">
          <input
            v-model="chatInput"
            type="text"
            placeholder="输入你的问题..."
            :disabled="!canChat || (phase !== 'ready' && phase !== 'summarizing') || chatLoading"
            class="flex-1 px-4 py-2.5 rounded-full border border-border-light text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary disabled:opacity-50"
          />
          <button
            type="submit"
            :disabled="!chatInput.trim() || chatLoading || !canChat"
            class="px-5 py-2.5 rounded-full bg-primary text-white text-sm font-medium hover:bg-primary-dark transition-colors disabled:opacity-50 cursor-pointer"
          >
            发送
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { startAnalyze, streamAnalyze, chatAnalyze, rewriteAnalyze } from '../api/analyze.js'
import { chatHistoryAnalyze, rewriteHistoryAnalyze } from '../api/history.js'
import { translateSubtitles } from '../api/video.js'
import MindMapView from './MindMapView.vue'
import { downloadSegments } from '../utils/subtitleExport.js'
import { downloadSummaryMarkdown, downloadSummaryPdf } from '../utils/summaryExport.js'
import { parseTimeString, buildVideoUrlWithTimestamp } from '../utils/timeUtils.js'
import { renderMarkdown } from '../utils/markdownRender.js'
import { useAuth } from '../composables/useAuth.js'

const { refreshUser } = useAuth()

const props = defineProps({
  url: { type: String, default: '' },
  fileId: { type: String, default: '' },
  localMode: Boolean,
  embedded: Boolean,
  videoUrl: { type: String, default: '' },
  thumbnail: { type: String, default: '' },
  isLoggedIn: { type: Boolean, default: false },
  initialHistory: { type: Object, default: null },
  historyId: { type: Number, default: null },
  demoMode: { type: Boolean, default: false },
  videoDuration: { type: Number, default: 0 },
})

const emit = defineEmits(['close', 'completed', 'sync-history', 'seek-video', 'upgrade-required', 'transcript-available', 'transcript-unavailable'])

const tabs = [
  { id: 'summary', label: '摘要' },
  { id: 'transcript', label: '转录' },
  { id: 'mindmap', label: '思维导图' },
  { id: 'article', label: '文章' },
  { id: 'chat', label: 'AI 问答' },
]

const visibleTabs = computed(() =>
  props.demoMode ? tabs.filter(t => t.id !== 'chat') : tabs
)

const activeTab = ref('summary')
const sessionId = ref('')
const meta = ref({})
const segments = ref([])
const summary = ref({})
const streamingSummary = ref('')
const mindmap = ref('')
const phase = ref('preparing')
const error = ref('')
const chatInput = ref('')
const chatMessages = ref([])
const chatLoading = ref(false)
const chatContainer = ref(null)
const mindmapRef = ref(null)
const transcriptContainer = ref(null)
const segmentRefs = ref({})
const highlightSegment = ref(-1)
const translating = ref(false)
const translateLang = ref('en')
const articleContent = ref('')
const articleStreaming = ref(false)
const rewriteLoading = ref(false)
const historySaved = ref(false)
const authRetryPending = ref(false)
const restoredMode = ref(false)
const historyRecordId = ref(null)

const canChat = computed(() => !!(sessionId.value || historyRecordId.value))
const canRewrite = computed(() => !!(sessionId.value || (historyRecordId.value && segments.value.length)))

const subtitleFormats = [
  { id: 'srt', label: 'SRT' },
  { id: 'vtt', label: 'VTT' },
  { id: 'txt', label: 'TXT' },
]

const translateLangs = [
  { id: 'en', label: 'English' },
  { id: 'zh', label: '中文' },
  { id: 'ja', label: '日本語' },
  { id: 'ko', label: '한국어' },
  { id: 'es', label: 'Español' },
  { id: 'fr', label: 'Français' },
]

const statusText = computed(() => {
  if (phase.value === 'preparing') return '正在准备分析...'
  if (phase.value === 'transcribing') {
    const mins = props.videoDuration > 0 ? Math.max(1, Math.round(props.videoDuration / 60)) : 0
    if (mins > 0) {
      return `正在下载并转写音频（约 ${mins} 分钟视频，无字幕时可能需 1–3 分钟）...`
    }
    return '正在下载并转写音频（无字幕视频可能需 1–3 分钟）...'
  }
  if (phase.value === 'summarizing') return 'AI 正在生成摘要与思维导图...'
  if (rewriteLoading.value) return 'AI 正在改写文章...'
  return ''
})

const renderedArticle = computed(() => renderMarkdown(articleContent.value))

function buildTimestampUrl(timeStr) {
  const seconds = parseTimeString(timeStr)
  return buildVideoUrlWithTimestamp(props.videoUrl || props.url, seconds)
}

function jumpToChapter(ch, index) {
  if (!props.demoMode) {
    activeTab.value = 'transcript'
  }
  const seconds = parseTimeString(ch.time)
  if (props.localMode && !props.demoMode) {
    emit('seek-video', seconds)
  }
  if (props.demoMode) {
    return
  }
  nextTick(() => {
    let targetIdx = 0
    for (let i = 0; i < segments.value.length; i++) {
      if (segments.value[i].start <= seconds) targetIdx = i
      else break
    }
    highlightSegment.value = targetIdx
    const el = segmentRefs.value[targetIdx]
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    setTimeout(() => { highlightSegment.value = -1 }, 2500)
    if (typeof index === 'number') {
      const chapterEl = document.getElementById('chapter-' + index)
      chapterEl?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  })
}

function exportMarkdown() {
  downloadSummaryMarkdown({
    title: meta.value.title,
    platform: meta.value.platform,
    url: props.url,
    summary: summary.value,
    mindmap: mindmap.value,
  })
}

function exportPdf() {
  downloadSummaryPdf({
    title: meta.value.title,
    platform: meta.value.platform,
    url: props.url,
    summary: summary.value,
    mindmap: mindmap.value,
    article: articleContent.value,
  })
}

async function handleTranslateDownload() {
  translating.value = true
  error.value = ''
  try {
    const response = await translateSubtitles(props.url, translateLang.value, 'srt')
    const contentDisposition = response.headers['content-disposition']
    let filename = `subtitle_${translateLang.value}.srt`
    if (contentDisposition) {
      const match = contentDisposition.match(/filename\*?=(?:UTF-8'')?([^;\n]+)/i)
      if (match) filename = decodeURIComponent(match[1].replace(/"/g, ''))
    }
    const blob = new Blob([response.data], { type: 'application/x-subrip;charset=utf-8' })
    const blobUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = filename
    a.click()
    URL.revokeObjectURL(blobUrl)
  } catch (err) {
    const msg = err.message || '字幕翻译失败'
    error.value = msg
    if (err.code) emit('upgrade-required', err.code)
  } finally {
    translating.value = false
  }
}

async function startRewrite() {
  if (rewriteLoading.value || !canRewrite.value) return
  rewriteLoading.value = true
  articleContent.value = ''
  articleStreaming.value = true

  const onEvent = (event) => {
    if (event.type === 'rewrite_chunk') {
      articleContent.value += event.content || ''
    } else if (event.type === 'rewrite_done') {
      articleContent.value = event.content || articleContent.value
      articleStreaming.value = false
    } else if (event.type === 'error') {
      error.value = event.message
      articleStreaming.value = false
    }
  }

  try {
    if (sessionId.value) {
      await rewriteAnalyze(sessionId.value, onEvent)
    } else if (historyRecordId.value) {
      await rewriteHistoryAnalyze(historyRecordId.value, onEvent)
    }
  } catch (err) {
    error.value = err.message || '文章改写失败'
    if (err.code) emit('upgrade-required', err.code)
  } finally {
    rewriteLoading.value = false
    articleStreaming.value = false
    if (articleContent.value) syncToHistory()
  }
}

function buildHistoryPayload(partial = false) {
  return {
    url: props.url || `local://${props.fileId}`,
    source: props.localMode ? 'local' : 'url',
    title: meta.value.title,
    platform: meta.value.platform,
    thumbnail: props.thumbnail,
    summary: { ...summary.value },
    mindmap: mindmap.value,
    segments: segments.value,
    transcriptSource: meta.value.transcript_source || '',
    article: articleContent.value,
    chatHistory: chatMessages.value
      .filter(m => !m.streaming)
      .map(m => ({ role: m.role, content: m.content })),
    partial,
  }
}

function syncToHistory() {
  if (!props.isLoggedIn || !summary.value.summary) return
  emit('sync-history', buildHistoryPayload(true))
}

function saveToHistory() {
  if (historySaved.value || restoredMode.value || !summary.value.summary) return
  historySaved.value = true
  emit('completed', buildHistoryPayload(false))
}

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

function exportTranscript(format) {
  if (!segments.value.length) return
  downloadSegments(segments.value, meta.value.title || 'subtitle', format)
}

watch(activeTab, async (tab) => {
  if (tab === 'mindmap') {
    await nextTick()
    mindmapRef.value?.fitMindmap()
  }
})

watch(() => props.isLoggedIn, (loggedIn) => {
  if (loggedIn && authRetryPending.value && phase.value === 'error') {
    authRetryPending.value = false
    historySaved.value = false
    runAnalysis()
  }
})

function isTranscriptUnavailableError(message) {
  if (!message) return false
  return /未检测到足够的人声|语音转写未识别|无法获取视频转录|无法获取视频字幕|转录内容均为|人声内容占比|未检测到可转写/.test(message)
}

function applyRestoredHistory(data) {
  restoredMode.value = true
  historyRecordId.value = data.id
  phase.value = 'ready'
  meta.value = {
    title: data.title,
    platform: data.platform,
    transcript_source: data.transcriptSource || null,
  }
  summary.value = data.summary || {}
  mindmap.value = data.mindmap || ''
  segments.value = data.segments || []
  articleContent.value = data.article || ''
  chatMessages.value = (data.chatHistory || []).map(m => ({
    role: m.role,
    content: m.content,
    streaming: false,
  }))
  if (data.segments?.length) {
    emit('transcript-available')
  } else {
    emit('transcript-unavailable')
  }
}

async function runAnalysis() {
  if (!props.url && !props.fileId) {
    phase.value = 'error'
    error.value = '缺少视频来源'
    return
  }
  phase.value = 'preparing'
  error.value = ''
  authRetryPending.value = false
  try {
    phase.value = 'transcribing'
    const res = await startAnalyze({
      url: props.url || undefined,
      fileId: props.fileId || undefined,
    })
    if (!res.success) throw new Error(res.error || '分析失败')

    await refreshUser()

    sessionId.value = res.data.session_id
    meta.value = res.data
    emit('transcript-available')

    phase.value = 'summarizing'
    await streamAnalyze(sessionId.value, handleStreamEvent)
    // 流结束但未收到 summary_done 时的兜底
    if (!summary.value.summary && streamingSummary.value) {
      summary.value = { summary: streamingSummary.value, highlights: [], chapters: [], terms: [] }
      streamingSummary.value = ''
    }
    if (phase.value !== 'error') {
      phase.value = 'ready'
      saveToHistory()
    }
  } catch (err) {
    phase.value = 'error'
    error.value = err.message || '分析失败，请稍后重试'
    if (isTranscriptUnavailableError(error.value)) {
      emit('transcript-unavailable')
    }
    if (err.code === 'AUTH_REQUIRED' || err.code === 'AUTH_EXPIRED') {
      authRetryPending.value = true
    }
    if (err.code === 'QUOTA_EXCEEDED') {
      await refreshUser()
    }
    if (err.code) emit('upgrade-required', err.code)
  }
}

function handleStreamEvent(event) {
  if (event.type === 'transcript') {
    segments.value = event.segments || []
  } else if (event.type === 'summary_chunk') {
    streamingSummary.value += event.content || ''
  } else if (event.type === 'summary_done') {
    summary.value = {
      summary: event.summary,
      highlights: event.highlights,
      chapters: event.chapters,
      terms: event.terms,
    }
    streamingSummary.value = ''
  } else if (event.type === 'mindmap') {
    mindmap.value = event.content || ''
  } else if (event.type === 'error') {
    error.value = event.message
    phase.value = 'error'
    if (isTranscriptUnavailableError(event.message)) {
      emit('transcript-unavailable')
    }
  }
}

async function sendChat() {
  const msg = chatInput.value.trim()
  if (!msg || !canChat.value || chatLoading.value) return

  chatInput.value = ''
  chatMessages.value.push({ role: 'user', content: msg })
  const assistantIdx = chatMessages.value.length
  chatMessages.value.push({ role: 'assistant', content: '', streaming: true })
  chatLoading.value = true

  await nextTick()
  if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight

  const onEvent = (event) => {
    if (event.type === 'chat_chunk') {
      chatMessages.value[assistantIdx].content += event.content || ''
    } else if (event.type === 'chat_done') {
      chatMessages.value[assistantIdx].content = event.content || chatMessages.value[assistantIdx].content
      chatMessages.value[assistantIdx].streaming = false
    } else if (event.type === 'error') {
      chatMessages.value[assistantIdx].content = event.message
      chatMessages.value[assistantIdx].streaming = false
    }
    nextTick(() => {
      if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    })
  }

  try {
    if (sessionId.value) {
      await chatAnalyze(sessionId.value, msg, onEvent)
      syncToHistory()
    } else if (historyRecordId.value) {
      await chatHistoryAnalyze(historyRecordId.value, msg, onEvent)
    }
  } catch (err) {
    chatMessages.value[assistantIdx].content = err.message
    chatMessages.value[assistantIdx].streaming = false
  } finally {
    chatLoading.value = false
    chatMessages.value[assistantIdx].streaming = false
  }
}

watch(() => props.historyId, (id) => {
  if (id) historyRecordId.value = id
})

onMounted(() => {
  if (props.initialHistory) {
    applyRestoredHistory(props.initialHistory)
    return
  }
  runAnalysis()
})
</script>
