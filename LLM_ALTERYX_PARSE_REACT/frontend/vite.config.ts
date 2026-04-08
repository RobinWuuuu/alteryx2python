import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// If port 9721 is stuck (e.g. orphaned uvicorn), run backend on another port and set:
//   VITE_API_PROXY_TARGET=http://127.0.0.1:9722
const apiProxy =
  process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:9721'

export default defineConfig({
  plugins: [react()],
  base: './',
  server: {
    port: 5200,
    proxy: {
      '/api': {
        target: apiProxy,
        changeOrigin: true,
      },
    },
  },
})
