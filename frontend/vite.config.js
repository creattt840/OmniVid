import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { seoBuildPlugin } from './plugins/seo-build.js'

export default defineConfig({
  plugins: [vue(), tailwindcss(), seoBuildPlugin()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
