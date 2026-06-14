<template>
  <header class="sticky top-0 z-50 bg-bg-card/90 backdrop-blur-md border-b border-border-light">
    <div class="page-container h-14 sm:h-16 flex items-center justify-between">
      <!-- 汉堡菜单 -->
      <button
        @click="$emit('menu-open')"
        class="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
        aria-label="打开菜单"
        aria-haspopup="dialog"
      >
        <svg class="w-5 h-5 text-text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <!-- Logo -->
      <a href="/" class="flex items-center gap-2 absolute left-1/2 -translate-x-1/2">
        <div class="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
          <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z" />
          </svg>
        </div>
        <span class="font-semibold text-text-primary hidden sm:inline">OmniVid</span>
      </a>

      <!-- 用户区 -->
      <div class="flex items-center gap-1">
        <button
          @click="$emit('history')"
          class="w-9 h-9 rounded-full hover:bg-gray-100 flex items-center justify-center transition-all cursor-pointer relative"
          aria-label="分析历史"
        >
          <svg class="w-5 h-5 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span
            v-if="historyCount > 0"
            class="absolute -top-0.5 -right-0.5 w-4 h-4 bg-primary text-white text-[10px] font-bold rounded-full flex items-center justify-center"
          >
            {{ historyCount > 9 ? '9+' : historyCount }}
          </span>
        </button>
        <button
          @click="$emit('login')"
          class="w-9 h-9 rounded-full bg-gradient-to-br from-primary/20 to-primary-light flex items-center justify-center hover:ring-2 hover:ring-primary/30 transition-all cursor-pointer"
          aria-label="登录"
        >
          <svg class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
defineProps({
  historyCount: { type: Number, default: 0 },
})

defineEmits(['login', 'history', 'menu-open'])
</script>
