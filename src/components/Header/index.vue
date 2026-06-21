<template>
  <header class="navbar">
    <div class="navbar-container">
      <div class="navbar-left">
        <router-link to="/" class="navbar-logo">
          <span>知识图谱系统</span>
        </router-link>
      </div>
      <nav class="navbar-nav">
        <router-link to="/" class="navbar-link">首页</router-link>
        <router-link to="/upload" class="navbar-link">文件上传</router-link>
        <router-link to="/extraction" class="navbar-link">知识抽取</router-link>
        <router-link to="/kg-build" class="navbar-link">图谱构建</router-link>
        <router-link to="/kg-visual" class="navbar-link">图谱可视化</router-link>
        <router-link to="/qa" class="navbar-link">智能问答</router-link>
      </nav>
      <div class="navbar-right">
        <el-dropdown v-if="userStore.isAuthenticated" @command="handleCommand">
          <div class="user-info">
            <el-avatar :size="32" class="user-avatar">
              {{ userStore.user?.nickname?.charAt(0) || userStore.user?.username?.charAt(0) || 'U' }}
            </el-avatar>
            <span class="user-name">{{ userStore.user?.nickname || userStore.user?.username }}</span>
            <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人信息</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <router-link v-else to="/login" class="login-link">登录</router-link>
      </div>
    </div>
  </header>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { useUserStore } from '../../store/userStore'

const router = useRouter()
const userStore = useUserStore()

const handleCommand = async (command) => {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      await userStore.logout()
      ElMessage.success('已退出登录')
      router.push('/login')
    } catch {
      // 用户取消
    }
  } else if (command === 'profile') {
    router.push('/profile')
  }
}
</script>

<style scoped>
.navbar {
  background: white;
  border-bottom: 1px solid #ebeef5;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 12px 0;
  position: sticky;
  top: 0;
  z-index: 1000;
  width: 100%;
}

.navbar-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
}

.navbar-left {
  display: flex;
  align-items: center;
}

.navbar-logo {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
}

.navbar-nav {
  display: flex;
  gap: 32px;
  align-items: center;
}

.navbar-link {
  color: #606266;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.3s;
  position: relative;
  padding: 4px 0;
}

.navbar-link::after {
  content: '';
  position: absolute;
  width: 0;
  height: 2px;
  bottom: 0;
  left: 0;
  background: #1890ff;
  transition: width 0.3s;
}

.navbar-link:hover {
  color: #1890ff;
}

.navbar-link.router-link-active {
  color: #1890ff;
}

.navbar-link:hover::after,
.navbar-link.router-link-active::after {
  width: 100%;
}

.navbar-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.3s;
}

.user-info:hover {
  background: #f5f7fa;
}

.user-avatar {
  background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
}

.user-name {
  font-size: 14px;
  color: #303133;
}

.login-link {
  color: #1890ff;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.3s;
}

.login-link:hover {
  color: #40a9ff;
}
</style>