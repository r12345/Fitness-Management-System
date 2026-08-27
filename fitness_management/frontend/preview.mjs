import { preview } from "vite";
import vue from "@vitejs/plugin-vue";

const server = await preview({
  configFile: false,
  root: process.cwd(),
  plugins: [vue()],
  preview: {
    port: 4173
  }
});

server.printUrls();
