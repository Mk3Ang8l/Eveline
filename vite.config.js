import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        timeout: 600000,
        proxyTimeout: 600000,
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        // FORCE CACHE BUSTING - V2
        entryFileNames: `assets/[name].v2.${Date.now()}.js`,
        chunkFileNames: `assets/[name].v2.${Date.now()}.js`,
        assetFileNames: `assets/[name].v2.${Date.now()}.[ext]`
      }
    }
  }
})
