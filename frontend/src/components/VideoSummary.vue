<template>
  <div class="mt-6 bg-bg-card rounded-3xl border border-border-light shadow-sm overflow-hidden animate-fade-up">
    <!-- 头部 -->
    <div class="px-5 sm:px-6 py-4 border-b border-border-light flex items-center justify-between gap-3">
      <div class="flex items-center gap-2 min-w-0">
        <span class="text-xl">🤖</span>
        <div class="min-w-0">
          <h3 class="font-bold text-text-primary truncate">AI 视频分析</h3>
          <p class="text-xs text-text-muted truncate">
            {{ meta.title }}
            <span v-if="meta.transcript_source" class="ml-1">
              · {{ meta.transcript_source === 'subtitle' ? '字幕提取' : '语音转写' }}
            </span>
          </p>
        </div>
      </div>
      <button
        @click="$emit('close')"
        class="flex-shrink-0 p-2 rounded-xl hover:bg-gray-100 text-text-muted transition-colors cursor-pointer"
        aria-label="关闭"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- 状态栏 -->
    <div v-if="phase !== 'ready'" class="px-5 sm:px-6 py-3 bg-primary-light/50 border-b border-border-light">
      <div class="flex items-center gap-2 text-sm text-primary">
        <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span>{{ statusText }}</span>
      </div>
    </div>

    <!-- 错误 -->
    <div v-if="error" class="px-5 sm:px-6 py-4 bg-red-50 text-red-700 text-sm">
      {{ error }}
    </div>

    <!-- Tabs -->
    <div class="flex border-b border-border-light overflow-x-auto">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        :class="[
          'flex-shrink-0 px-5 py-3 text-sm font-medium transition-colors cursor-pointer border-b-2 -mb-px',
          activeTab === tab.id
            ? 'border-primary text-primary'
            : 'border-transparent text-text-muted hover:text-text-primary'
        ]"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab 内容 -->
    <div class="p-5 sm:p-6 min-h-[280px] max-h-[520px] overflow-y-auto">
      <!-- 摘要 -->
      <div v-show="activeTab === 'summary'" class="space-y-5">
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
            <div class="h-4 w-16 bg-gray-200 rounded animate-pulse mb-3" />
            <div class="space-y-2">
              <div class="h-3 bg-gray-100 rounded animate-pulse" />
              <div class="h-3 bg-gray-100 rounded animate-pulse w-5/6" />
              <div class="h-3 bg-gray-100 rounded animate-pulse w-4/6" />
            </div>
          </section>
          <section class="py-2">
            <div class="h-4 w-20 bg-gray-200 rounded animate-pulse mb-3" />
            <div class="space-y-2">
              <div v-for="n in 3" :key="n" class="h-3 bg-gray-100 rounded animate-pulse" :class="n === 3 ? 'w-2/3' : ''" />
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
                class="p-3 rounded-2xl bg-gray-50 border border-border-light"
              >
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-xs font-mono text-primary bg-primary-light px-2 py-0.5 rounded-lg">{{ ch.time }}</span>
                  <span class="text-sm font-medium text-text-primary">{{ ch.title }}</span>
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

      <!-- 转录 -->
      <div v-show="activeTab === 'transcript'">
        <div v-if="segments.length" class="space-y-2">
          <div class="flex items-center gap-2 pb-2 border-b border-border-light">
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
          </div>
          <div class="space-y-1 font-mono text-xs">
            <div
              v-for="(seg, i) in segments"
              :key="i"
              class="flex gap-3 py-1.5 hover:bg-gray-50 rounded-lg px-2 -mx-2"
            >
              <span class="text-primary flex-shrink-0 w-14">{{ formatTime(seg.start) }}</span>
              <span class="text-text-secondary leading-relaxed">{{ seg.text }}</span>
            </div>
          </div>
        </div>
        <p v-else class="text-sm text-text-muted text-center py-8">转录文本加载中...</p>
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

      <!-- AI 问答 -->
      <div v-show="activeTab === 'chat'" class="flex flex-col h-[380px]">
        <div ref="chatContainer" class="flex-1 overflow-y-auto space-y-3 mb-4 pr-1">
          <div v-if="!chatMessages.length" class="text-sm text-text-muted text-center py-8">
            基于视频内容提问，例如：「视频的核心观点是什么？」
          </div>
          <div
            v-for="(msg, i) in chatMessages"
            :key="i"
            :class="[
              'max-w-[85%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed',
              msg.role === 'user'
                ? 'ml-auto bg-primary text-white rounded-br-md'
                : 'bg-gray-100 text-text-secondary rounded-bl-md'
            ]"
          >
            {{ msg.content }}
            <span v-if="msg.streaming" class="inline-block w-1.5 h-3.5 bg-current opacity-60 animate-pulse ml-0.5" />
          </div>
        </div>
        <form @submit.prevent="sendChat" class="flex gap-2">
          <input
            v-model="chatInput"
            type="text"
            placeholder="输入你的问题..."
            :disabled="phase !== 'ready' && phase !== 'summarizing' || chatLoading"
            class="flex-1 px-4 py-2.5 rounded-full border border-border-light text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary disabled:opacity-50"
          />
          <button
            type="submit"
            :disabled="!chatInput.trim() || chatLoading || !sessionId"
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
import { startAnalyze, streamAnalyze, chatAnalyze } from '../api/analyze.js'
import MindMapView from './MindMapView.vue'
import { downloadSegments } from '../utils/subtitleExport.js'

const props = defineProps({
  url: { type: String, required: true },
})

defineEmits(['close'])

const tabs = [
  { id: 'summary', label: '摘要' },
  { id: 'transcript', label: '转录' },
  { id: 'mindmap', label: '思维导图' },
  { id: 'chat', label: 'AI 问答' },
]

const activeTab = ref('summary')
const sessionId = ref('')
const meta = ref({})
const segments = ref([])
const summary = ref({})
const streamingSummary = ref('')
const mindmap = ref('')
const phase = ref('preparing') // preparing | transcribing | summarizing | ready | error
const error = ref('')
const chatInput = ref('')
const chatMessages = ref([])
const chatLoading = ref(false)
const chatContainer = ref(null)
const mindmapRef = ref(null)

const subtitleFormats = [
  { id: 'srt', label: 'SRT' },
  { id: 'vtt', label: 'VTT' },
  { id: 'txt', label: 'TXT' },
]

const statusText = computed(() => {
  if (phase.value === 'preparing') return '正在准备分析...'
  if (phase.value === 'transcribing') return '正在提取/转写视频文本...'
  if (phase.value === 'summarizing') return 'AI 正在生成摘要与思维导图...'
  return ''
})

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

async function runAnalysis() {
  phase.value = 'preparing'
  error.value = ''
  try {
    phase.value = 'transcribing'
    const res = await startAnalyze(props.url)
    if (!res.success) throw new Error(res.error || '分析失败')

    sessionId.value = res.data.session_id
    meta.value = res.data

    phase.value = 'summarizing'
    await streamAnalyze(sessionId.value, handleStreamEvent)
    // 流结束但未收到 summary_done 时的兜底
    if (!summary.value.summary && streamingSummary.value) {
      summary.value = { summary: streamingSummary.value, highlights: [], chapters: [], terms: [] }
      streamingSummary.value = ''
    }
    if (phase.value !== 'error') phase.value = 'ready'
  } catch (err) {
    phase.value = 'error'
    error.value = err.message || '分析失败，请稍后重试'
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
  }
}

async function sendChat() {
  const msg = chatInput.value.trim()
  if (!msg || !sessionId.value || chatLoading.value) return

  chatInput.value = ''
  chatMessages.value.push({ role: 'user', content: msg })
  const assistantIdx = chatMessages.value.length
  chatMessages.value.push({ role: 'assistant', content: '', streaming: true })
  chatLoading.value = true

  await nextTick()
  if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight

  try {
    await chatAnalyze(sessionId.value, msg, (event) => {
      if (event.type === 'chat_chunk') {
        chatMessages.value[assistantIdx].content += event.content || ''
      } else if (event.type === 'chat_done') {
        chatMessages.value[assistantIdx].streaming = false
      } else if (event.type === 'error') {
        chatMessages.value[assistantIdx].content = event.message
        chatMessages.value[assistantIdx].streaming = false
      }
      nextTick(() => {
        if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
      })
    })
  } catch (err) {
    chatMessages.value[assistantIdx].content = err.message
    chatMessages.value[assistantIdx].streaming = false
  } finally {
    chatLoading.value = false
    chatMessages.value[assistantIdx].streaming = false
  }
}

onMounted(runAnalysis)
</script>
