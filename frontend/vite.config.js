import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// El backend FastAPI corre en el puerto 8000. Vite redirige hacia allí
// tanto las peticiones REST (/api) como el canal WebSocket (/ws), para
// que el frontend pueda usar rutas relativas y no haya problemas de CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
      },
    },
  },
})
