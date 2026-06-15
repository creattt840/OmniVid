<template>
  <section id="pricing" class="py-14 sm:py-20 bg-bg-card border-t border-border-light" aria-labelledby="pricing-heading">
    <div class="page-container">
      <div class="text-center mb-10 sm:mb-14">
        <h2 id="pricing-heading" class="section-title mb-3">
          选择适合你的<span class="text-primary">下载方案</span>
        </h2>
        <p class="section-desc">
          登录后每日免费 10 次 AI 分析，满足日常视频学习需求
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-5 max-w-4xl mx-auto">
        <!-- 免费版 -->
        <div class="card-surface p-7 flex flex-col ring-2 ring-primary/20">
          <div class="mb-5">
            <div class="inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary-light text-primary mb-2">
              当前方案
            </div>
            <h3 class="text-lg font-bold text-text-primary mb-1">免费版</h3>
            <p class="text-sm text-text-secondary">登录即可使用全部核心功能</p>
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
            class="w-full h-12 rounded-lg bg-primary text-white text-sm font-semibold hover:bg-primary-dark transition-colors cursor-pointer"
            @click="$emit('need-login')"
          >
            {{ isLoggedIn ? '立即使用' : '免费使用' }}
          </button>
        </div>

        <!-- 会员版（暂未开放） -->
        <div class="relative bg-gradient-to-br from-gray-400 to-gray-500 rounded-2xl p-7 flex flex-col text-white overflow-hidden shadow-xl opacity-90">
          <div class="absolute top-4 right-4 px-3 py-1 bg-white/20 rounded-full text-xs font-semibold backdrop-blur-sm">
            暂未开放
          </div>
          <div class="absolute -top-20 -right-20 w-56 h-56 bg-white/5 rounded-full" />
          <div class="relative">
            <div class="mb-5">
              <h3 class="text-lg font-bold mb-1">VIP 高级版</h3>
              <p class="text-sm text-white/70">更多权益即将上线</p>
            </div>
            <div class="mb-6">
              <span class="text-4xl font-bold">—</span>
            </div>
            <ul class="space-y-3 mb-8">
              <li v-for="item in vipPlan" :key="item" class="flex items-start gap-2.5 text-sm text-white/80">
                <svg class="w-5 h-5 text-white/50 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                {{ item }}
              </li>
            </ul>
            <button
              class="w-full h-12 rounded-lg bg-white/20 text-white font-semibold text-sm cursor-not-allowed"
              disabled
            >
              暂未开放
            </button>
            <p class="text-center text-xs text-white/50 mt-3">会员功能筹备中，敬请期待</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  isLoggedIn: { type: Boolean, default: false },
})

defineEmits(['need-login'])

const freePlan = [
  '1800+ 平台视频下载',
  '多种清晰度可选',
  '每日 10 次 AI 视频分析',
  'AI 改写文章 + 字幕翻译',
  '笔记 Markdown / PDF 导出',
  '云端分析历史（10 条）',
]

const vipPlan = [
  '更高每日分析额度',
  '4K 超清优先下载',
  '优先解析队列',
  '更多高级功能',
]
</script>
