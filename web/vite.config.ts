import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import { fileURLToPath } from 'node:url'

export default defineConfig(({ mode }) => {
  const projectRoot = fileURLToPath(new URL('../', import.meta.url))
  const { BACKEND_PORT = '8000' } = loadEnv(mode, projectRoot, 'BACKEND_PORT')

  return {
    plugins: [react()],
    server: {
      host: '127.0.0.1',
      proxy: {
        '/escenarios': process.env.PULSO_API_TARGET || `http://127.0.0.1:${BACKEND_PORT}`,
      },
    },
  }
})
