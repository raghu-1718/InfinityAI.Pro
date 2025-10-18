import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Default resolve; we avoid __dirname in TS typing for simplicity
  server: { port: 5173, host: true },
  preview: { port: 5174 }
})
