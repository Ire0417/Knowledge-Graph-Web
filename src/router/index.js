import { createRouter, createWebHistory } from 'vue-router'
import { useFileStore } from '../store/fileStore'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/Home/index.vue')
    },
    {
      path: '/upload',
      name: 'upload',
      component: () => import('../views/Upload/index.vue')
    },
    {
      path: '/kg-build',
      name: 'kg-build',
      component: () => import('../views/KgBuild/index.vue')
    },
    {
      path: '/kg-visual',
      name: 'kg-visual',
      component: () => import('../views/KgVisual/index.vue')
    },
    {
      path: '/qa',
      name: 'qa',
      component: () => import('../views/Qa/index.vue')
    }
  ]
})

// 路由守卫
router.beforeEach((to, from) => {
  const fileStore = useFileStore()
  
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