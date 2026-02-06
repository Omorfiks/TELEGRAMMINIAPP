import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

// Функция для получения SSL сертификатов
function getHttpsConfig() {
  // Для локальной разработки через туннель используем HTTP
  // Cloudflare автоматически добавит HTTPS на публичном URL
  const useHttps = process.env.USE_LOCAL_HTTPS === 'true'
  
  if (!useHttps) {
    return false // Используем HTTP для cloudflared туннеля
  }
  
  // Проверяем различные варианты имен файлов сертификатов
  const certPaths = [
    path.resolve(__dirname, 'certs/localhost+1.pem'),
    path.resolve(__dirname, 'certs/localhost.pem'),
    path.resolve(__dirname, 'certs/localhost.crt'),
  ]
  const keyPaths = [
    path.resolve(__dirname, 'certs/localhost+1-key.pem'),
    path.resolve(__dirname, 'certs/localhost-key.pem'),
    path.resolve(__dirname, 'certs/localhost.key'),
  ]
  
  for (let i = 0; i < certPaths.length; i++) {
    if (fs.existsSync(certPaths[i]) && fs.existsSync(keyPaths[i])) {
      console.log(`✅ Найден SSL сертификат: ${path.basename(certPaths[i])}`)
      return {
        key: fs.readFileSync(keyPaths[i]),
        cert: fs.readFileSync(certPaths[i]),
      }
    }
  }
  
  return false
}

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    https: getHttpsConfig(),
    hmr: {
      clientPort: 5173
    }
  },
  preview: {
    host: '0.0.0.0',
    port: 5173,
    https: getHttpsConfig(),
  }
})
