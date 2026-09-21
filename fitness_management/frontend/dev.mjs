import { createServer } from "vite";
import vue from "@vitejs/plugin-vue";

const server = await createServer({
  configFile: false,
  root: process.cwd(),
  plugins: [vue()],
  server: {
    host: "localhost",
    port: Number(process.env.PORT || 5173),
    proxy: {
      "/api": {
        // 后端 main.py 里 uvicorn 跑在 8001，前端 api/request.js 也直连 8001。
        // 这里原来写 8000，代理其实是走不到的（仅作为备用入口，别再改成别的端口）
        target: "http://127.0.0.1:8001",
        changeOrigin: true
      }
    }
  }
});

await server.listen();
server.printUrls();
