<template>
  <section id="features" class="py-14 sm:py-20 bg-bg-card border-y border-border-light" aria-labelledby="features-heading">
    <div class="page-container">
      <div class="text-center mb-10 sm:mb-14">
        <h2 id="features-heading" class="section-title mb-3">
          为什么选择<span class="text-primary">我们</span>
        </h2>
        <p class="section-desc">
          比平台自带下载更自由，比浏览器插件更方便，手机电脑都能用
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
        <div
          v-for="feature in features"
          :key="feature.title"
          class="card-surface card-surface-lift p-6"
        >
          <div class="w-12 h-12 rounded-lg flex items-center justify-center mb-4" :class="feature.bg">
            <span class="w-6 h-6 text-primary" v-html="feature.icon" />
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
const iconGlobe = `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"/></svg>`
const iconPhone = `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>`
const iconFilm = `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"/></svg>`
const iconDroplet = `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>`
const iconSparkles = `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z"/></svg>`
const iconNotes = `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/></svg>`
const iconBolt = `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"/></svg>`

const features = [
  {
    icon: iconGlobe,
    title: '1800+ 平台全覆盖',
    desc: 'YouTube、Bilibili、抖音、TikTok、Twitter 等主流平台一网打尽，持续更新。',
    bg: 'bg-blue-50',
  },
  {
    icon: iconPhone,
    title: '手机也能下载',
    desc: '响应式设计，手机浏览器粘贴链接即可下载，无需安装 App。',
    bg: 'bg-green-50',
  },
  {
    icon: iconFilm,
    title: '多种清晰度可选',
    desc: '从 360P 到 4K，自由选择最适合的清晰度，A/V 自动合并。',
    bg: 'bg-purple-50',
  },
  {
    icon: iconDroplet,
    title: '抖音无水印下载',
    desc: '专用解析引擎，自动去除抖音水印，获取原始高清视频。',
    bg: 'bg-indigo-50',
    badge: '独家',
    badgeClass: 'bg-indigo-100 text-primary-dark',
  },
  {
    icon: iconSparkles,
    title: 'AI 视频总结',
    desc: '摘要、思维导图、AI 改写、字幕翻译与笔记导出，快速掌握核心内容。',
    bg: 'bg-amber-50',
    badge: '已上线',
    badgeClass: 'bg-green-100 text-green-700',
  },
  {
    icon: iconNotes,
    title: '笔记导出与历史',
    desc: '一键导出 Markdown/PDF 笔记，本地保存分析历史，随时回看。',
    bg: 'bg-rose-50',
    badge: '新功能',
    badgeClass: 'bg-indigo-100 text-primary-dark',
  },
  {
    icon: iconBolt,
    title: '极速解析下载',
    desc: '智能路由选择最优解析方案，10 秒内完成解析，下载速度有保障。',
    bg: 'bg-indigo-50',
  },
]
</script>
