<template>
  <div class="min-h-screen flex flex-col bg-bg-page">
    <AppHeader @login="showComingSoon('登录注册')" />

    <main class="flex-1">
      <HeroSection
        @parse="handleParse"
        :loading="loading"
        :compact="!!videoData"
        :showSlogan="!videoData"
      />

      <!-- 解析结果 -->
      <section v-if="videoData" class="pb-8 sm:pb-12 animate-fade-up">
        <div class="max-w-2xl mx-auto px-4 sm:px-6">
          <VideoResult
            :video="videoData"
            :downloading="downloading"
            :errorMsg="downloadError"
            @download="handleDownload"
          />
        </div>
      </section>

      <!-- 解析错误提示 -->
      <div v-if="parseError" class="max-w-2xl mx-auto px-4 sm:px-6 -mt-4 mb-6">
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
import { ref } from 'vue'
import AppHeader from './components/AppHeader.vue'
import HeroSection from './components/HeroSection.vue'
import VideoResult from './components/VideoResult.vue'
import PlatformSection from './components/PlatformSection.vue'
import FeatureSection from './components/FeatureSection.vue'
import HowToSection from './components/HowToSection.vue'
import PricingSection from './components/PricingSection.vue'
import AppFooter from './components/AppFooter.vue'
import { parseVideo, downloadViaServer } from './api/video.js'

const loading = ref(false)
const downloading = ref(false)
const videoData = ref(null)
const currentUrl = ref('')
const parseError = ref('')
const downloadError = ref('')
const toast = ref(null)

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
  currentUrl.value = url

  try {
    const res = await parseVideo(url)
    if (res.success) {
      videoData.value = res.data
      showToast('解析成功！选择清晰度后点击下载', 'success')
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
    const response = await downloadViaServer(currentUrl.value, formatId)
    const contentDisposition = response.headers['content-disposition']
    let filename = 'video.mp4'
    if (contentDisposition) {
      const match = contentDisposition.match(/filename\*?=(?:UTF-8'')?([^;\n]+)/i)
      if (match) filename = decodeURIComponent(match[1].replace(/"/g, ''))
    }
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    window.URL.revokeObjectURL(url)
    showToast('下载已开始，请查看浏览器下载列表', 'success')
  } catch (err) {
    downloadError.value = err.message || '下载失败，请稍后重试'
  } finally {
    downloading.value = false
  }
}
</script>

<style>
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, -10px); }
</style>
