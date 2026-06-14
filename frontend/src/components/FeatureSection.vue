<template>
  <section id="features" class="py-14 sm:py-20 bg-bg-card" aria-labelledby="features-heading">
    <div class="page-container">
      <div class="text-center mb-10 sm:mb-14">
        <h2 id="features-heading" class="text-2xl sm:text-3xl font-bold text-text-primary mb-3">
          为什么选择<span class="text-primary">我们</span>
        </h2>
        <p class="text-text-secondary max-w-lg mx-auto">
          比平台自带下载更自由，比浏览器插件更方便，手机电脑都能用
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
        <div
          v-for="feature in features"
          :key="feature.title"
          class="p-6 rounded-3xl border border-border-light hover:border-primary/20 hover:shadow-md transition-all"
        >
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl mb-4" :class="feature.bg">
            {{ feature.icon }}
          </div>
          <h3 class="font-bold text-text-primary mb-2">{{ feature.title }}</h3>
          <p class="text-sm text-text-secondary leading-relaxed">{{ feature.desc }}</p>
          <div v-if="feature.badge" class="mt-3">
            <span class="inline-block px-2.5 py-0.5 text-xs font-medium rounded-full" :class="feature.badgeClass">
              {{ feature.badge }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
const features = [
  {
    icon: '🌐',
    title: '1800+ 平台全覆盖',
    desc: 'YouTube、Bilibili、抖音、TikTok、Twitter 等主流平台一网打尽，持续更新。',
    bg: 'bg-blue-50',
  },
  {
    icon: '📱',
    title: '手机也能下载',
    desc: '响应式设计，手机浏览器粘贴链接即可下载，无需安装 App。',
    bg: 'bg-green-50',
  },
  {
    icon: '🎬',
    title: '多种清晰度可选',
    desc: '从 360P 到 4K，自由选择最适合的清晰度，A/V 自动合并。',
    bg: 'bg-purple-50',
  },
  {
    icon: '💧',
    title: '抖音无水印下载',
    desc: '专用解析引擎，自动去除抖音水印，获取原始高清视频。',
    bg: 'bg-indigo-50',
    badge: '独家',
    badgeClass: 'bg-indigo-100 text-primary-dark',
  },
  {
    icon: '🤖',
    title: 'AI 视频总结',
    desc: '摘要、思维导图、AI 改写、字幕翻译与笔记导出，快速掌握核心内容。',
    bg: 'bg-amber-50',
    badge: '已上线',
    badgeClass: 'bg-green-100 text-green-700',
  },
  {
    icon: '📝',
    title: '笔记导出与历史',
    desc: '一键导出 Markdown/PDF 笔记，本地保存分析历史，随时回看。',
    bg: 'bg-rose-50',
    badge: '新功能',
    badgeClass: 'bg-indigo-100 text-primary-dark',
  },
  {
    icon: '⚡',
    title: '极速解析下载',
    desc: '智能路由选择最优解析方案，10 秒内完成解析，下载速度有保障。',
    bg: 'bg-indigo-50',
  },
]
</script>
