<template>
  <div class="min-h-screen flex flex-col bg-bg-page">
    <AppHeader
      :history-count="historyItems.length"
      @login="showComingSoon('登录注册')"
      @history="historyOpen = true"
      @menu-open="menuOpen = true"
    />

    <main class="flex-1">
      <HeroSection
        @parse="handleParse"
        :loading="loading"
        :compact="!!videoData"
        :showSlogan="!videoData"
      />

      <!-- 解析结果：统一卡片双栏工作区 -->
      <section v-if="videoData" class="pb-8 sm:pb-12 animate-fade-up">
        <div class="page-container">
          <div class="bg-bg-card rounded-3xl border border-border-light shadow-sm overflow-hidden">
            <div class="grid grid-cols-1 lg:grid-cols-5 items-start divide-y lg:divide-y-0 lg:divide-x divide-border-light">
              <div class="lg:col-span-2">
                <VideoResult
                  ref="videoResultRef"
                  compact
                  workspace
                  :local-mode="sourceMode === 'local'"
                  :preview-url="previewUrl"
                  :video="videoData"
                  :downloading="downloading"
                  :downloadingSubtitles="downloadingSubtitles"
                  :subtitleLoadingText="subtitleLoadingText"
                  :errorMsg="downloadError"
                  @download="handleDownload"
                  @download-subtitles="handleDownloadSubtitles"
                />
              </div>
              <div v-if="showSummary" class="lg:col-span-3 flex flex-col overflow-hidden max-h-[520px] sm:max-h-[580px] lg:max-h-[640px]">
                <VideoSummary
                  :key="summaryKey"
                  embedded
                  :url="currentUrl"
                  :file-id="fileId"
                  :local-mode="sourceMode === 'local'"
                  :video-url="sourceMode === 'url' ? currentUrl : ''"
                  :thumbnail="videoData?.thumbnail || ''"
                  @completed="handleAnalysisCompleted"
                  @seek-video="handleSeekVideo"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 解析错误提示 -->
      <div v-if="parseError" class="page-container -mt-4 mb-6">
        <div class="flex items-start gap-3 p-4 rounded-2xl bg-red-50 border border-red-100 text-red-700 text-sm">
          <svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <span>{{ parseError }}</span>
        </div>
      </div>

      <PlatformSection />
      <FeatureSection />
      <HowToSection />
      <PricingSection
        @need-login="showComingSoon('登录注册')"
        @open-vip="showComingSoon('VIP 付费')"
      />
    </main>

    <AppFooter />

    <HistoryPanel
      :open="historyOpen"
      :items="historyItems"
      @close="historyOpen = false"
      @select="handleHistorySelect"
      @remove="handleHistoryRemove"
      @clear="handleHistoryClear"
    />

    <SideMenuDrawer
      :open="menuOpen"
      :history-count="historyItems.length"
      @close="menuOpen = false"
      @new-parse="handleNewParse"
      @history="handleMenuHistory"
      @upload-local="handleMenuUploadLocal"
      @navigate="handleMenuNavigate"
    />

    <LocalUploadModal
      :open="uploadModalOpen"
      @close="uploadModalOpen = false"
      @success="handleUploadSuccess"
    />

    <!-- Toast 提示 -->
    <Teleport to="body">
      <Transition name="toast">
        <div
          v-if="toast"
          class="fixed top-20 left-1/2 -translate-x-1/2 z-[200] px-5 py-3 rounded-2xl shadow-xl border text-sm font-medium"
          :class="toast.type === 'success'
            ? 'bg-green-50 border-green-200 text-green-800'
            : 'bg-bg-card border-border text-text-primary'"
        >
          {{ toast.message }}
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import AppHeader from './components/AppHeader.vue'
import HeroSection from './components/HeroSection.vue'
import VideoResult from './components/VideoResult.vue'
import VideoSummary from './components/VideoSummary.vue'
import HistoryPanel from './components/HistoryPanel.vue'
import SideMenuDrawer from './components/SideMenuDrawer.vue'
import LocalUploadModal from './components/LocalUploadModal.vue'
import PlatformSection from './components/PlatformSection.vue'
import FeatureSection from './components/FeatureSection.vue'
import HowToSection from './components/HowToSection.vue'
import PricingSection from './components/PricingSection.vue'
import AppFooter from './components/AppFooter.vue'
import { parseVideo, downloadViaServer, downloadSubtitles, getDirectUrl, downloadFromDirectUrl, triggerBlobDownload, parseFilenameFromDisposition } from './api/video.js'
import { getUploadStreamUrl } from './api/upload.js'
import { loadHistory, saveHistoryItem, removeHistoryItem, clearHistory } from './utils/historyStore.js'

const loading = ref(false)
const downloading = ref(false)
const downloadingSubtitles = ref(false)
const subtitleLoadingText = ref('字幕处理中...')
const videoData = ref(null)
const currentUrl = ref('')
const fileId = ref('')
const sourceMode = ref('url') // 'url' | 'local'
const parseError = ref('')
const downloadError = ref('')
const toast = ref(null)
const showSummary = ref(false)
const historyOpen = ref(false)
const historyItems = ref([])
const menuOpen = ref(false)
const uploadModalOpen = ref(false)
const videoResultRef = ref(null)

const previewUrl = computed(() => {
  if (sourceMode.value === 'local' && fileId.value) {
    return getUploadStreamUrl(fileId.value)
  }
  return ''
})

/** 切换视频来源时强制重建 VideoSummary，避免复用旧分析状态 */
const summaryKey = computed(() =>
  sourceMode.value === 'local' ? `local:${fileId.value}` : `url:${currentUrl.value}`,
)

onMounted(() => {
  historyItems.value = loadHistory()
})

function refreshHistory() {
  historyItems.value = loadHistory()
}

function handleAnalysisCompleted(item) {
  saveHistoryItem(item)
  refreshHistory()
}

function handleHistorySelect(url) {
  historyOpen.value = false
  if (url.startsWith('local://')) {
    showToast('本地文件会话已过期，请重新上传', 'info')
    uploadModalOpen.value = true
    return
  }
  handleParse(url)
}

function handleHistoryRemove(id) {
  removeHistoryItem(id)
  refreshHistory()
}

function handleHistoryClear() {
  clearHistory()
  refreshHistory()
}

function resetWorkspace() {
  videoData.value = null
  showSummary.value = false
  currentUrl.value = ''
  fileId.value = ''
  sourceMode.value = 'url'
  parseError.value = ''
  downloadError.value = ''
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function handleNewParse() {
  resetWorkspace()
  menuOpen.value = false
}

function handleMenuHistory() {
  menuOpen.value = false
  historyOpen.value = true
}

function handleMenuUploadLocal() {
  menuOpen.value = false
  uploadModalOpen.value = true
}

async function handleUploadSuccess(data) {
  resetWorkspace()
  // 等待卸载旧 VideoSummary，避免同 tick 批处理导致组件复用、残留上次分析
  await nextTick()
  sourceMode.value = 'local'
  fileId.value = data.file_id
  videoData.value = data
  showSummary.value = true
  showToast('上传成功，正在生成 AI 摘要...', 'success')
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function handleSeekVideo(seconds) {
  videoResultRef.value?.seekTo(seconds)
}

function handleMenuNavigate(href) {
  menuOpen.value = false
  document.querySelector(href)?.scrollIntoView({ behavior: 'smooth' })
}

function showToast(message, type = 'info') {
  toast.value = { message, type }
  setTimeout(() => { toast.value = null }, 3000)
}

function showComingSoon(feature) {
  showToast(`${feature}功能将在第 4-6 阶段上线，敬请期待`)
}

async function handleParse(url) {
  loading.value = true
  videoData.value = null
  parseError.value = ''
  downloadError.value = ''
  showSummary.value = false
  currentUrl.value = url
  fileId.value = ''
  sourceMode.value = 'url'

  try {
    const res = await parseVideo(url)
    if (res.success) {
      videoData.value = res.data
      showSummary.value = true
      showToast('解析成功，正在生成 AI 摘要...', 'success')
    } else {
      parseError.value = res.error || '未知错误'
    }
  } catch (err) {
    const detail = err.response?.data?.detail
    parseError.value = typeof detail === 'object' ? detail.error : (detail || err.message || '请检查链接是否正确')
  } finally {
    loading.value = false
  }
}

async function handleDownload(formatId) {
  downloading.value = true
  downloadError.value = ''
  try {
    // 优先尝试直链下载（fetch → Blob），跨域 CDN 不能用 <a download> + target=_blank
    try {
      const directRes = await getDirectUrl(currentUrl.value, formatId)
      if (directRes.success && directRes.data?.direct_url) {
        const { direct_url, ext, title } = directRes.data
        const filename = `${title || 'video'}.${ext || 'mp4'}`
        const ok = await downloadFromDirectUrl(direct_url, filename)
        if (ok) {
          showToast('直链下载已开始', 'success')
          return
        }
      }
    } catch {
      // 直链不可用，回退服务端代理
    }

    const response = await downloadViaServer(currentUrl.value, formatId)
    const filename = parseFilenameFromDisposition(response.headers['content-disposition'])
    triggerBlobDownload(new Blob([response.data]), filename)
    showToast('下载已开始（服务端代理）', 'success')
  } catch (err) {
    downloadError.value = err.message || '下载失败，请稍后重试'
  } finally {
    downloading.value = false
  }
}

async function handleDownloadSubtitles() {
  downloadingSubtitles.value = true
  subtitleLoadingText.value = videoData.value?.subtitles?.length
    ? '正在提取字幕...'
    : '正在语音转写，请稍候...'
  downloadError.value = ''
  try {
    const response = await downloadSubtitles(currentUrl.value, 'srt')
    const source = response.headers['x-transcript-source']
    if (source === 'whisper') {
      subtitleLoadingText.value = '语音转写完成，正在保存...'
    }
    const filename = parseFilenameFromDisposition(response.headers['content-disposition'], 'subtitle.srt')
    triggerBlobDownload(new Blob([response.data], { type: 'application/x-subrip;charset=utf-8' }), filename)
    const msg = source === 'whisper' ? '字幕已生成（语音转写）并开始下载' : '字幕下载已开始'
    showToast(msg, 'success')
  } catch (err) {
    const detail = err.response?.data?.detail
    downloadError.value = typeof detail === 'object' ? detail.error : (detail || err.message || '字幕下载失败')
  } finally {
    downloadingSubtitles.value = false
    subtitleLoadingText.value = '字幕处理中...'
  }
}

</script>

<style>
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, -10px); }
</style>
