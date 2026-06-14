<template>
  <div class="mindmap-wrapper">
    <!-- 工具栏 -->
    <div v-if="content" class="flex items-center justify-end gap-2 mb-2">
      <button
        type="button"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium text-text-secondary hover:bg-gray-100 border border-border-light transition-colors cursor-pointer"
        title="全屏查看"
        @click="toggleFullscreen"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
        </svg>
        全屏
      </button>
      <div ref="exportMenuRef" class="relative">
        <button
          type="button"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium text-primary hover:bg-primary-light border border-primary/30 transition-colors cursor-pointer"
          :disabled="exporting"
          @click="showExportMenu = !showExportMenu"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          {{ exporting ? '导出中...' : '下载' }}
        </button>
        <div
          v-if="showExportMenu"
          class="absolute right-0 top-full mt-1 z-10 min-w-[120px] py-1 bg-white rounded-xl border border-border-light shadow-lg"
        >
          <button
            v-for="item in exportOptions"
            :key="item.format"
            type="button"
            class="block w-full text-left px-4 py-2 text-xs text-text-secondary hover:bg-gray-50 cursor-pointer"
            @click="handleExport(item.format)"
          >
            {{ item.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- 内嵌视图 -->
    <div
      ref="containerRef"
      class="mindmap-container"
      :class="{ 'mindmap-container--hidden': isFullscreen }"
    >
      <svg ref="svgRef" class="mindmap-svg mindmap-svg--inline" />
    </div>

    <!-- 全屏视图 -->
    <Teleport to="body">
      <div
        v-if="isFullscreen"
        ref="fullscreenOverlayRef"
        class="fixed inset-0 z-[300] bg-white flex flex-col"
        tabindex="0"
        @keydown.esc="closeFullscreen"
      >
        <div class="flex items-center justify-between px-4 py-3 border-b border-border-light flex-shrink-0">
          <span class="text-sm font-medium text-text-primary truncate">{{ title || '思维导图' }}</span>
          <div class="flex items-center gap-2 flex-shrink-0">
            <button
              type="button"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium text-primary hover:bg-primary-light border border-primary/30 cursor-pointer"
              :disabled="exporting"
              @click="handleExport('png')"
            >
              下载 PNG
            </button>
            <button
              type="button"
              class="p-2 rounded-xl hover:bg-gray-100 text-text-muted cursor-pointer"
              aria-label="退出全屏"
              @click="closeFullscreen"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        <div ref="fullscreenContainerRef" class="flex-1 mindmap-container mindmap-container--fullscreen">
          <svg ref="fullscreenSvgRef" class="mindmap-svg mindmap-svg--fullscreen" />
        </div>
      </div>
    </Teleport>

    <p v-if="!content && !error" class="text-sm text-text-muted text-center py-8">暂无思维导图</p>
    <p v-if="error" class="text-sm text-red-600 text-center py-4">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Markmap } from 'markmap-view'
import { Transformer } from 'markmap-lib'
import {
  exportMindmapMarkdown,
  exportMindmapPng,
  exportMindmapSvg,
} from '../utils/mindmapExport.js'

const props = defineProps({
  content: { type: String, default: '' },
  title: { type: String, default: '思维导图' },
})

const containerRef = ref(null)
const svgRef = ref(null)
const fullscreenContainerRef = ref(null)
const fullscreenSvgRef = ref(null)
const fullscreenOverlayRef = ref(null)
const exportMenuRef = ref(null)
const error = ref('')
const isFullscreen = ref(false)
const showExportMenu = ref(false)
const exporting = ref(false)

let markmapInstance = null
let fullscreenMarkmapInstance = null
let resizeObserver = null
const transformer = new Transformer()

const exportOptions = [
  { format: 'png', label: 'PNG 图片' },
  { format: 'svg', label: 'SVG 矢量' },
  { format: 'md', label: 'Markdown' },
]

const markmapOptions = {
  autoFit: true,
  duration: 300,
  maxWidth: 280,
  color: (node) => {
    const colors = ['#6366F1', '#818CF8', '#4F46E5', '#A5B4FC', '#7C3AED']
    return colors[(node.state?.depth || 0) % colors.length]
  },
}

async function renderMindmap() {
  error.value = ''
  if (!props.content?.trim() || !svgRef.value) return

  await nextTick()
  try {
    const { root } = transformer.transform(props.content)
    if (!markmapInstance) {
      markmapInstance = Markmap.create(svgRef.value, markmapOptions, root)
    } else {
      markmapInstance.setData(root)
      markmapInstance.fit()
    }
    if (isFullscreen.value && fullscreenSvgRef.value) {
      await renderFullscreenMindmap(root)
    }
  } catch (e) {
    error.value = '思维导图渲染失败'
    console.error(e)
  }
}

async function renderFullscreenMindmap(root) {
  if (!fullscreenSvgRef.value) return
  await nextTick()
  if (!fullscreenMarkmapInstance) {
    fullscreenMarkmapInstance = Markmap.create(fullscreenSvgRef.value, markmapOptions, root)
  } else {
    fullscreenMarkmapInstance.setData(root)
    fullscreenMarkmapInstance.fit()
  }
}

async function toggleFullscreen() {
  isFullscreen.value = true
  document.body.style.overflow = 'hidden'
  await nextTick()
  fullscreenOverlayRef.value?.focus()
  if (props.content?.trim()) {
    const { root } = transformer.transform(props.content)
    await renderFullscreenMindmap(root)
  }
}

function closeFullscreen() {
  isFullscreen.value = false
  document.body.style.overflow = ''
  fullscreenMarkmapInstance = null
}

async function handleExport(format) {
  showExportMenu.value = false
  if (format === 'md') {
    exportMindmapMarkdown(props.content, props.title)
    return
  }

  const svgEl = isFullscreen.value ? fullscreenSvgRef.value : svgRef.value
  const containerEl = isFullscreen.value ? fullscreenContainerRef.value : containerRef.value
  if (!svgEl) {
    error.value = '思维导图尚未渲染完成'
    return
  }

  exporting.value = true
  error.value = ''
  try {
    if (format === 'png') {
      await exportMindmapPng(containerEl, svgEl, props.title)
    } else if (format === 'svg') {
      await exportMindmapSvg(containerEl, svgEl, props.title)
    }
  } catch (e) {
    error.value = e.message || '导出失败'
    console.error('思维导图导出失败:', e)
  } finally {
    exporting.value = false
  }
}

function fitMindmap() {
  markmapInstance?.fit()
  fullscreenMarkmapInstance?.fit()
}

function onDocumentClick(e) {
  if (exportMenuRef.value && !exportMenuRef.value.contains(e.target)) {
    showExportMenu.value = false
  }
}

watch(() => props.content, renderMindmap)

onMounted(() => {
  renderMindmap()
  document.addEventListener('click', onDocumentClick)
  if (containerRef.value) {
    resizeObserver = new ResizeObserver(() => fitMindmap())
    resizeObserver.observe(containerRef.value)
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  resizeObserver?.disconnect()
  document.body.style.overflow = ''
  markmapInstance = null
  fullscreenMarkmapInstance = null
})

defineExpose({ fitMindmap })
</script>

<style scoped>
.mindmap-wrapper {
  width: 100%;
}
.mindmap-container {
  width: 100%;
  min-height: 320px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 1rem;
  border: 1px solid var(--color-border-light, #e5e7eb);
  overflow: hidden;
}
.mindmap-container--hidden {
  visibility: hidden;
  position: absolute;
  pointer-events: none;
  height: 0;
  min-height: 0;
  overflow: hidden;
}
.mindmap-container--fullscreen {
  border: none;
  border-radius: 0;
  min-height: 0;
}
.mindmap-svg {
  width: 100%;
  display: block;
}
.mindmap-svg--inline {
  height: 400px;
}
.mindmap-svg--fullscreen {
  height: calc(100vh - 56px);
}
</style>
