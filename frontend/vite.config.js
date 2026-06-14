import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(), // Tailwind CSS v4 Vite plugin — no separate config file needed
  ],
  server: {
    port: 5173,
    // Proxy API calls to Django so we avoid CORS issues during development.
    // e.g. /api/users/ → http://localhost:8000/api/users/
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
