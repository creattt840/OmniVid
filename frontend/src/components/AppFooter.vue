<template>
  <footer class="border-t border-border-light bg-bg-card mt-auto" :class="minimal ? 'py-4' : ''">
    <div class="page-container" :class="minimal ? 'py-4' : 'py-8 sm:py-10'">
      <template v-if="!minimal">
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-8 mb-8">
          <div>
            <div class="flex items-center gap-2 mb-3">
              <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-primary to-primary-dark flex items-center justify-center">
                <svg class="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              </div>
              <span class="text-sm font-bold text-text-primary">OmniVid</span>
            </div>
            <p class="text-sm text-text-secondary leading-relaxed">
              智能视频助理，一键保存。下载与 AI 总结同屏完成。
            </p>
          </div>
          <div>
            <h4 class="text-sm font-semibold text-text-primary mb-3">产品</h4>
            <ul class="space-y-2 text-sm text-text-secondary">
              <li><a href="#platforms" class="hover:text-primary transition-colors">支持平台</a></li>
              <li><a href="#features" class="hover:text-primary transition-colors">功能亮点</a></li>
              <li><a href="#pricing" class="hover:text-primary transition-colors">定价方案</a></li>
            </ul>
          </div>
          <div>
            <h4 class="text-sm font-semibold text-text-primary mb-3">声明</h4>
            <p class="text-xs text-text-muted leading-relaxed">
              本站仅供个人学习交流使用，请勿用于商业或侵权用途。下载内容的版权归原作者所有。
            </p>
          </div>
        </div>
        <div class="pt-4 border-t border-border-light text-center text-xs text-text-muted space-y-1">
          <p>© {{ year }} OmniVid · 基于 yt-dlp 开源项目</p>
          <p v-if="icpNumber">
            <a
              v-if="icpLink"
              :href="icpLink"
              target="_blank"
              rel="noopener noreferrer"
              class="hover:text-primary transition-colors"
            >{{ icpNumber }}</a>
            <span v-else>{{ icpNumber }}</span>
          </p>
        </div>
      </template>
      <div v-else class="text-center text-xs text-text-muted space-y-1">
        <p>© {{ year }} OmniVid · 仅供个人学习交流使用</p>
        <p v-if="icpNumber">
          <a
            v-if="icpLink"
            :href="icpLink"
            target="_blank"
            rel="noopener noreferrer"
            class="hover:text-primary transition-colors"
          >{{ icpNumber }}</a>
          <span v-else>{{ icpNumber }}</span>
        </p>
      </div>
    </div>
  </footer>
</template>

<script setup>
defineProps({
  minimal: { type: Boolean, default: false },
})

const year = new Date().getFullYear()
const icpNumber = (import.meta.env.VITE_ICP_NUMBER || '').trim()
const icpLink = (import.meta.env.VITE_ICP_LINK || 'https://beian.miit.gov.cn/').trim()
</script>
