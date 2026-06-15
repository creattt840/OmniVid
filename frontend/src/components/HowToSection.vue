<template>
  <section id="howto" class="py-14 sm:py-20" aria-labelledby="howto-heading">
    <div class="page-container">
      <div class="text-center mb-10 sm:mb-14">
        <h2 id="howto-heading" class="section-title mb-3">
          三步<span class="text-primary">轻松下载</span>
        </h2>
        <p class="section-desc">无需注册，无需安装，打开网页就能用</p>
      </div>

      <div class="relative grid grid-cols-1 sm:grid-cols-3 gap-8 sm:gap-6">
        <div
          class="hidden sm:block absolute top-7 left-[calc(16.67%+1rem)] right-[calc(16.67%+1rem)] h-px bg-border"
          aria-hidden="true"
        />
        <div v-for="(step, i) in steps" :key="step.title" class="relative text-center">
          <div class="relative inline-flex items-center justify-center w-14 h-14 rounded-lg bg-primary-light text-primary text-lg font-bold mb-4">
            {{ String(i + 1).padStart(2, '0') }}
          </div>
          <h3 class="font-bold text-text-primary mb-2">{{ step.title }}</h3>
          <p class="text-sm text-text-secondary leading-relaxed max-w-xs mx-auto">{{ step.desc }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
const steps = [
  { title: '复制视频链接', desc: '在 YouTube、Bilibili、抖音等平台复制视频分享链接' },
  { title: '粘贴并解析', desc: '将链接粘贴到上方搜索框，点击「解析」获取视频信息' },
  { title: '选择并下载', desc: '选择想要的清晰度，点击「立即下载」保存到本地' },
]
</script>
