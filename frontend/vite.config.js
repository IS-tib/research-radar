import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In development the frontend runs on http://localhost:5173 and the backend on
// http://localhost:8000; this proxy forwards requests under /api to the
// backend so calls can target "/api/papers" directly, without hardcoding a
// port. Production uses the VITE_API_URL env var instead (see src/api.js).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
