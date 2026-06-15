<template>
  <div class="flex flex-wrap items-center justify-center gap-6 sm:gap-10 mt-8 sm:mt-10">
    <div
      v-for="stat in stats"
      :key="stat.label"
      class="text-center min-w-[5.5rem]"
    >
      <div class="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
        {{ stat.value }}
      </div>
      <div class="text-xs sm:text-sm text-text-muted mt-1">{{ stat.label }}</div>
    </div>
  </div>
</template>

<script setup>
const stats = [
  { value: '1800+', label: '视频平台' },
  { value: '5 种', label: 'AI 输出' },
  { value: '6 语言', label: '字幕翻译' },
]
</script>
