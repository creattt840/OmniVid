<template>
  <footer class="border-t border-border-light bg-bg-card mt-auto">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
      <div class="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-primary flex items-center justify-center">
            <svg class="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
          <span class="text-sm font-medium text-text-primary">万能视频下载器</span>
        </div>
        <p class="text-xs text-text-muted text-center max-w-md">
          本站仅供个人学习交流使用，请勿用于商业或侵权用途。下载内容的版权归原作者所有。
        </p>
      </div>
      <div class="mt-4 pt-4 border-t border-border-light text-center text-xs text-text-muted">
        © {{ year }} 万能视频下载器 · 基于 yt-dlp 开源项目
      </div>
    </div>
  </footer>
</template>

<script setup>
const year = new Date().getFullYear()
</script>
