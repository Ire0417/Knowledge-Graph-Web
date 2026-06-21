import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3006, // 前端服务端口
    open: true, // 自动打开浏览器
    proxy: {
      // 代理API请求到Python后端
      "/api": {
        target: "http://localhost:8000", // FastAPI后端地址（uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload）
        changeOrigin: true, // 解决跨域问题
        rewrite: (path) => path.replace(/^\/api/, ""), // 移除/api前缀
      },
    },
  },
  build: {
    outDir: "dist",
    assetsDir: "assets",
    sourcemap: false,
  },
});