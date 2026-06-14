<template>
  <header class="sticky top-0 z-50 bg-bg-card/90 backdrop-blur-md border-b border-border-light">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
      <!-- 汉堡菜单 -->
      <button
        @click="menuOpen = !menuOpen"
        class="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
        aria-label="打开菜单"
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
        <span class="font-semibold text-text-primary hidden sm:inline">万能视频下载</span>
      </a>

      <!-- 用户区 -->
      <button
        @click="$emit('login')"
        class="w-9 h-9 rounded-full bg-gradient-to-br from-primary/20 to-blue-100 flex items-center justify-center hover:ring-2 hover:ring-primary/30 transition-all cursor-pointer"
        aria-label="登录"
      >
        <svg class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      </button>
    </div>

    <!-- 移动端菜单 -->
    <Transition name="slide">
      <nav v-if="menuOpen" class="sm:hidden border-t border-border-light bg-bg-card px-4 py-3 space-y-1">
        <a v-for="item in navItems" :key="item.href" :href="item.href"
          @click="menuOpen = false"
          class="block px-3 py-2.5 rounded-xl text-sm text-text-secondary hover:bg-gray-50 hover:text-primary transition-colors">
          {{ item.label }}
        </a>
      </nav>
    </Transition>
  </header>
</template>

<script setup>
import { ref } from 'vue'

defineEmits(['login'])

const menuOpen = ref(false)
const navItems = [
  { label: '支持平台', href: '#platforms' },
  { label: '功能亮点', href: '#features' },
  { label: '使用教程', href: '#howto' },
  { label: 'VIP 套餐', href: '#pricing' },
]
</script>

<style scoped>
.slide-enter-active, .slide-leave-active { transition: all 0.2s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
