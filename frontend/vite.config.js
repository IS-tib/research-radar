import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// During local development the frontend runs on http://localhost:5173 and the
// backend on http://localhost:8000. This "proxy" forwards any request starting
// with /api to the backend, so in your code you can just call "/api/papers"
// and not worry about ports. In production we use the VITE_API_URL env var
// instead (see src/api.js).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
