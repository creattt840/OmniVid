<template>
  <section id="pricing" class="py-14 sm:py-20 bg-bg-card border-t border-border-light" aria-labelledby="pricing-heading">
    <div class="page-container">
      <div class="text-center mb-10 sm:mb-14">
        <h2 id="pricing-heading" class="section-title mb-3">
          选择适合你的<span class="text-primary">下载方案</span>
        </h2>
        <p class="section-desc">
          免费版满足日常需求，VIP 解锁 AI 总结等全部高级功能
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-5 max-w-4xl mx-auto">
        <!-- 免费版 -->
        <div class="card-surface p-7 flex flex-col">
          <div class="mb-5">
            <h3 class="text-lg font-bold text-text-primary mb-1">免费版</h3>
            <p class="text-sm text-text-secondary">满足基础下载需求</p>
          </div>
          <div class="mb-6">
            <span class="text-4xl font-bold text-text-primary">¥0</span>
            <span class="text-text-muted text-sm ml-1">/永久</span>
          </div>
          <ul class="space-y-3 mb-8 flex-1">
            <li v-for="item in freePlan" :key="item" class="flex items-start gap-2.5 text-sm text-text-secondary">
              <svg class="w-5 h-5 text-success flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              {{ item }}
            </li>
          </ul>
          <button
            class="w-full h-12 rounded-lg border border-border text-sm font-semibold text-text-primary hover:bg-surface-muted transition-colors cursor-pointer"
            @click="$emit('need-login')"
          >
            {{ isLoggedIn ? '立即使用' : '免费使用' }}
          </button>
        </div>

        <!-- VIP 版 -->
        <div class="relative bg-gradient-to-br from-primary to-primary-dark rounded-2xl p-7 flex flex-col text-white overflow-hidden shadow-xl">
          <div class="absolute top-4 right-4 px-3 py-1 bg-white/20 rounded-full text-xs font-semibold backdrop-blur-sm">
            最受欢迎
          </div>
          <div class="absolute -top-20 -right-20 w-56 h-56 bg-white/5 rounded-full" />
          <div class="relative">
            <div class="mb-5">
              <h3 class="text-lg font-bold mb-1">VIP 高级版</h3>
              <p class="text-sm text-white/70">解锁全部功能，无限制使用</p>
            </div>
            <div class="mb-6">
              <span class="text-4xl font-bold">¥9.9</span>
              <span class="text-white/70 text-sm ml-1">/月</span>
              <span class="ml-2 text-xs bg-white/20 px-2 py-0.5 rounded-full">限时优惠</span>
            </div>
            <ul class="space-y-3 mb-8">
              <li v-for="item in vipPlan" :key="item" class="flex items-start gap-2.5 text-sm text-white/90">
                <svg class="w-5 h-5 text-yellow-300 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                {{ item }}
              </li>
            </ul>
            <button
              class="w-full h-12 rounded-lg bg-white text-primary font-semibold text-sm hover:bg-white/90 transition-colors shadow-md cursor-pointer disabled:opacity-60"
              :disabled="checkoutLoading"
              @click="$emit('open-vip')"
            >
              {{ checkoutLoading ? '跳转支付中...' : (isVip ? '续费 VIP' : '开通 VIP') }}
            </button>
            <p v-if="isVip && vipExpiresAt" class="text-center text-xs text-white/60 mt-3">
              VIP 有效期至 {{ formatDate(vipExpiresAt) }}
            </p>
            <p v-else class="text-center text-xs text-white/50 mt-3">¥9.9 / 30 天 · Stripe 安全支付</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  isLoggedIn: { type: Boolean, default: false },
  isVip: { type: Boolean, default: false },
  vipExpiresAt: { type: String, default: '' },
  checkoutLoading: { type: Boolean, default: false },
})

defineEmits(['need-login', 'open-vip'])

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

const freePlan = [
  '1800+ 平台视频下载',
  '多种清晰度可选',
  '每日 3 次 AI 视频总结',
  '笔记 Markdown 导出',
  '标准解析速度',
]

const vipPlan = [
  '包含免费版全部功能',
  '无限 AI 视频总结',
  '4K 超清优先下载',
  '字幕翻译（6 语言）',
  '笔记 PDF 导出 + 分析历史',
  '优先解析队列',
  '无广告纯净体验',
]
</script>
