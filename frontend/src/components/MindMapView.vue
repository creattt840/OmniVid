<template>
  <div ref="containerRef" class="mindmap-container">
    <svg ref="svgRef" class="mindmap-svg" />
    <p v-if="!content && !error" class="text-sm text-text-muted text-center py-8">暂无思维导图</p>
    <p v-if="error" class="text-sm text-red-600 text-center py-4">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Markmap } from 'markmap-view'
import { Transformer } from 'markmap-lib'

const props = defineProps({
  content: { type: String, default: '' },
})

const containerRef = ref(null)
const svgRef = ref(null)
const error = ref('')
let markmapInstance = null
const transformer = new Transformer()

async function renderMindmap() {
  error.value = ''
  if (!props.content?.trim() || !svgRef.value) return

  await nextTick()
  try {
    const { root } = transformer.transform(props.content)
    if (!markmapInstance) {
      markmapInstance = Markmap.create(svgRef.value, {
        autoFit: true,
        duration: 300,
        maxWidth: 280,
        color: (node) => {
          const colors = ['#3B82F6', '#6366F1', '#8B5CF6', '#0EA5E9', '#14B8A6']
          return colors[(node.state?.depth || 0) % colors.length]
        },
      }, root)
    } else {
      markmapInstance.setData(root)
      markmapInstance.fit()
    }
  } catch (e) {
    error.value = '思维导图渲染失败'
    console.error(e)
  }
}

watch(() => props.content, renderMindmap)

onMounted(renderMindmap)
onBeforeUnmount(() => {
  markmapInstance = null
})
</script>

<style scoped>
.mindmap-container {
  width: 100%;
  min-height: 320px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 1rem;
  border: 1px solid var(--color-border-light, #e5e7eb);
  overflow: hidden;
}
.mindmap-svg {
  width: 100%;
  height: 400px;
  display: block;
}
</style>
