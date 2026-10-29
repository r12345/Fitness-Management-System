import { defineConfig } from "vite";
import { fileURLToPath, URL } from "node:url";
import vue from "@vitejs/plugin-vue";
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  // .env 统一放在项目根（和后端共用一份），从前端目录往上是两级
  envDir: fileURLToPath(new URL("../../", import.meta.url)),
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
      dts: './auto-imports.d.ts'
    }),
    Components({
      resolvers: [ElementPlusResolver()],
      dts: './components.d.ts'
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true
      }
    }
  },
});
