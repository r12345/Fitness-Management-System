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
        target: "http://127.0.0.1:8000",
        changeOrigin: true
      }
    }
  }
});

await server.listen();
server.printUrls();
