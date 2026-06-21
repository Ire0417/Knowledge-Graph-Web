import { createRouter, createWebHistory } from 'vue-router'
import { useFileStore } from '../store/fileStore'
import { useUserStore } from '../store/userStore'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/Login/index.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      name: 'home',
      component: () => import('../views/Home/index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/upload',
      name: 'upload',
      component: () => import('../views/Upload/index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/kg-build',
      name: 'kg-build',
      component: () => import('../views/KgBuild/index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/kg-visual',
      name: 'kg-visual',
      component: () => import('../views/KgVisual/index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/qa',
      name: 'qa',
      component: () => import('../views/Qa/index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/Profile/index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/extraction',
      name: 'extraction',
      component: () => import('../views/Extraction/index.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

// 路由守卫
router.beforeEach((to, from) => {
  const userStore = useUserStore()
  const fileStore = useFileStore()
  
  // 检查是否需要登录
  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    return { name: 'login' }
  }
  
  // 如果已经登录，不允许访问登录页面
  if (to.name === 'login' && userStore.isAuthenticated) {
    return { name: 'home' }
  }
  
  // 检查是否需要上传文件才能访问的页面
  const requiresFile = ['kg-build', 'kg-visual', 'qa']
  
  if (requiresFile.includes(to.name) && !fileStore.uploadedFiles.length) {
    // 如果没有上传文件，重定向到上传页面
    return { name: 'upload' }
  }
  
  // 允许导航
  return true
})

export default router