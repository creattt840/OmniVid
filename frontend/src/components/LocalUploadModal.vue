<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="open"
        class="fixed inset-0 z-[160] flex items-center justify-center p-4"
        @click.self="!uploading && emit('close')"
      >
        <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" />
        <div
          class="relative w-full max-w-lg bg-bg-card rounded-3xl border border-border-light shadow-2xl overflow-hidden animate-fade-up"
          role="dialog"
          aria-label="上传本地视频"
        >
          <!-- 头部 -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
            <div>
              <h2 class="font-bold text-text-primary text-lg">本地视频上传</h2>
              <p class="text-xs text-text-muted mt-0.5">上传本地文件进行 AI 分析总结</p>
            </div>
            <button
              type="button"
              class="p-2 rounded-xl hover:bg-gray-100 text-text-muted cursor-pointer disabled:opacity-40"
              :disabled="uploading"
              aria-label="关闭"
              @click="emit('close')"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="px-6 py-5 space-y-4">
            <!-- 媒体文件拖拽区 -->
            <div
              class="relative border-2 border-dashed rounded-2xl p-6 text-center transition-colors cursor-pointer"
              :class="dragOver
                ? 'border-primary bg-primary-light/30'
                : mediaFile
                  ? 'border-primary/40 bg-primary-light/10'
                  : 'border-border hover:border-primary/40 hover:bg-gray-50'"
              @click="!uploading && mediaInput?.click()"
              @dragover.prevent="dragOver = true"
              @dragleave.prevent="dragOver = false"
              @drop.prevent="handleMediaDrop"
            >
              <input
                ref="mediaInput"
                type="file"
                class="hidden"
                accept=".mp4,.mkv,.mov,.webm,.avi,.mp3,.m4a,.wav,.aac,.ogg,video/*,audio/*"
                :disabled="uploading"
                @change="handleMediaSelect"
              />
              <svg class="w-10 h-10 mx-auto text-primary/60 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p v-if="mediaFile" class="text-sm font-medium text-text-primary truncate px-2">
                {{ mediaFile.name }}
              </p>
              <p v-else class="text-sm font-medium text-text-primary">点击或拖拽视频/音频文件</p>
              <p class="text-xs text-text-muted mt-1">
                支持 MP4、MKV、MOV、WebM、MP3 等 · 最大 500MB · 最长 60 分钟
              </p>
            </div>

            <!-- 可选字幕 -->
            <div class="flex items-center gap-3">
              <button
                type="button"
                class="flex-shrink-0 px-3 py-2 rounded-xl border border-border-light text-xs font-medium text-text-secondary hover:border-primary/40 hover:text-primary transition-colors cursor-pointer disabled:opacity-40"
                :disabled="uploading"
                @click="subtitleInput?.click()"
              >
                {{ subtitleFile ? '更换字幕' : '添加字幕（可选）' }}
              </button>
              <input
                ref="subtitleInput"
                type="file"
                class="hidden"
                accept=".srt,.vtt,text/vtt,application/x-subrip"
                :disabled="uploading"
                @change="handleSubtitleSelect"
              />
              <span v-if="subtitleFile" class="text-xs text-text-muted truncate flex-1">
                {{ subtitleFile.name }}
                <button
                  type="button"
                  class="ml-1 text-red-500 hover:underline cursor-pointer"
                  @click.stop="subtitleFile = null"
                >移除</button>
              </span>
              <span v-else class="text-xs text-text-muted">SRT / VTT，有字幕可跳过语音转写</span>
            </div>

            <!-- 进度条 -->
            <div v-if="uploading" class="space-y-2">
              <div class="flex justify-between text-xs text-text-muted">
                <span>{{ progress < 100 ? '上传中...' : '处理中...' }}</span>
                <span>{{ progress }}%</span>
              </div>
              <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  class="h-full bg-primary rounded-full transition-all duration-300"
                  :style="{ width: progress + '%' }"
                />
              </div>
              <p class="text-xs text-text-muted">长视频转写可能需要数分钟，请耐心等待</p>
            </div>

            <!-- 错误 -->
            <p v-if="error" class="text-sm text-red-600 bg-red-50 rounded-xl px-4 py-3">{{ error }}</p>
          </div>

          <!-- 底部操作 -->
          <div class="px-6 py-4 border-t border-border-light flex gap-3">
            <button
              type="button"
              class="flex-1 h-11 rounded-full border border-border-light text-text-secondary font-medium hover:bg-gray-50 transition-colors cursor-pointer disabled:opacity-40"
              :disabled="uploading"
              @click="emit('close')"
            >
              取消
            </button>
            <button
              type="button"
              class="flex-1 h-11 rounded-full bg-primary hover:bg-primary-dark text-white font-semibold transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="!mediaFile || uploading"
              @click="handleUpload"
            >
              {{ uploading ? '上传中...' : '开始分析' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { uploadLocalFile } from '../api/upload.js'

const props = defineProps({
  open: Boolean,
})

const emit = defineEmits(['close', 'success'])

const mediaInput = ref(null)
const subtitleInput = ref(null)
const mediaFile = ref(null)
const subtitleFile = ref(null)
const dragOver = ref(false)
const uploading = ref(false)
const progress = ref(0)
const error = ref('')

watch(() => props.open, (isOpen) => {
  if (!isOpen) resetForm()
})

function resetForm() {
  mediaFile.value = null
  subtitleFile.value = null
  dragOver.value = false
  uploading.value = false
  progress.value = 0
  error.value = ''
}

function pickMedia(file) {
  if (!file) return
  mediaFile.value = file
  error.value = ''
}

function handleMediaSelect(e) {
  pickMedia(e.target.files?.[0])
  e.target.value = ''
}

function handleMediaDrop(e) {
  dragOver.value = false
  if (uploading.value) return
  const file = e.dataTransfer.files?.[0]
  pickMedia(file)
}

function handleSubtitleSelect(e) {
  subtitleFile.value = e.target.files?.[0] || null
  e.target.value = ''
}

async function handleUpload() {
  if (!mediaFile.value || uploading.value) return
  uploading.value = true
  progress.value = 0
  error.value = ''
  try {
    const res = await uploadLocalFile(
      mediaFile.value,
      subtitleFile.value,
      (pct) => { progress.value = pct },
    )
    if (!res.success) throw new Error(res.error || '上传失败')
    progress.value = 100
    emit('success', res.data)
    emit('close')
  } catch (err) {
    error.value = err.message || '上传失败，请稍后重试'
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
@keyframes fade-up { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
.animate-fade-up { animation: fade-up 0.25s ease; }
</style>
