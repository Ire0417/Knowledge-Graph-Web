<template>
  <header class="navbar">
    <div class="navbar-container">
      <div class="navbar-left">
        <router-link to="/" class="navbar-logo">
          <span>知识图谱生成系统</span>
        </router-link>
      </div>
      <nav class="navbar-nav">
        <router-link to="/" class="navbar-link">首页</router-link>
        <router-link to="/upload" class="navbar-link">文件上传</router-link>
        <router-link to="/kg-build" class="navbar-link">图谱构建</router-link>
        <router-link to="/kg-visual" class="navbar-link">图谱可视化</router-link>
        <router-link to="/qa" class="navbar-link">智能问答</router-link>
      </nav>
    </div>
  </header>
</template>

<script setup>
// Header logic
</script>

<style scoped>
.navbar {
  /* 更透明的玻璃效果 */
  background: rgba(15, 15, 26, 0.6);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  /* 阴影让导航栏悬浮感更强 */
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
  padding: 16px 0;
  position: sticky;
  top: 0;
  z-index: 1000;
  width: 100%;
}

.navbar-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.navbar-left {
  display: flex;
  align-items: center;
}

.navbar-logo {
  font-size: 20px;
  font-weight: bold;
  color: var(--text-primary);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.navbar-logo:hover {
  transform: scale(1.05);
  text-shadow: 0 0 8px rgba(123, 44, 191, 0.5);
}

.logo-icon {
  font-size: 24px;
}

.navbar-nav {
  display: flex;
  gap: 32px;
  align-items: center;
}

.navbar-link {
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.3s ease;
  position: relative;
  padding: 4px 0;
}

/* 链接下划线动画 */
.navbar-link::after {
  content: '';
  position: absolute;
  width: 0;
  height: 2px;
  bottom: 0;
  left: 0;
  background: var(--primary-light);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 8px var(--primary-light);
}

.navbar-link:hover {
  color: #fff;
}

.navbar-link.router-link-active {
  color: #fff;
}

.navbar-link:hover::after, .navbar-link.router-link-active::after {
  width: 100%;
}

.btn-sm {
  padding: 8px 20px;
  font-size: 14px;
}

.glass-btn {
  background: rgba(123, 44, 191, 0.6);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.glass-btn:hover {
  background: rgba(157, 78, 221, 0.8);
  box-shadow: 0 0 15px rgba(123, 44, 191, 0.5);
}
</style>
