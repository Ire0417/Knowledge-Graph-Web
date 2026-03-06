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
        target: "http://localhost:5000", // Python后端地址
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