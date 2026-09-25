import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// Development: Vite serves the SPA and proxies /api to FastAPI (same origin for the cookie).
// Production: FastAPI serves the built SPA from dist/ (single origin, no CORS).
const API_TARGET = process.env.VITE_API_TARGET ?? 'http://127.0.0.1:8000' // 127.0.0.1, not localhost (CR-005)

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: API_TARGET, changeOrigin: false },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    passWithNoTests: true,
  },
})
