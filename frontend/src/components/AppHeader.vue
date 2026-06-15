<template>
  <header class="sticky top-0 z-50 bg-bg-card/90 backdrop-blur-md border-b border-border/60">
    <div class="page-container h-16 flex items-center gap-4">
      <!-- 左侧 -->
      <div class="flex items-center gap-3 flex-1 min-w-0">
        <button
          @click="$emit('menu-open')"
          class="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-surface-muted transition-colors cursor-pointer lg:hidden"
          aria-label="打开菜单"
          aria-haspopup="dialog"
        >
          <svg class="w-5 h-5 text-text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <a href="/" class="flex items-center gap-2 flex-shrink-0">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary-dark flex items-center justify-center shadow-sm">
            <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
          <span class="font-bold text-text-primary hidden sm:inline">OmniVid</span>
        </a>

        <nav v-if="!focusMode" class="hidden lg:flex items-center gap-1 ml-4">
          <button
            v-for="item in navItems"
            :key="item.href"
            type="button"
            class="px-3 py-1.5 text-sm text-text-secondary hover:text-primary rounded-lg hover:bg-surface-muted transition-colors cursor-pointer"
            @click="$emit('navigate', item.href)"
          >
            {{ item.label }}
          </button>
        </nav>

        <button
          v-if="focusMode"
          type="button"
          class="hidden sm:inline-flex btn-secondary h-9 px-4 text-sm ml-2"
          @click="$emit('new-parse')"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          新解析
        </button>
      </div>

      <!-- 右侧 -->
      <div class="flex items-center gap-1 flex-shrink-0">
        <button
          @click="$emit('upload-local')"
          class="w-9 h-9 rounded-lg hover:bg-surface-muted flex items-center justify-center transition-all cursor-pointer"
          aria-label="上传本地文件"
        >
          <svg class="w-5 h-5 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
        </button>
        <button
          @click="$emit('history')"
          class="w-9 h-9 rounded-lg hover:bg-surface-muted flex items-center justify-center transition-all cursor-pointer relative"
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
          class="w-9 h-9 rounded-lg bg-primary-light flex items-center justify-center hover:ring-2 hover:ring-primary/20 transition-all cursor-pointer"
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
  focusMode: { type: Boolean, default: false },
})

defineEmits(['login', 'history', 'menu-open', 'navigate', 'new-parse', 'upload-local'])

const navItems = [
  { label: '平台', href: '#platforms' },
  { label: '功能', href: '#features' },
  { label: '教程', href: '#howto' },
  { label: '定价', href: '#pricing' },
]
</script>
