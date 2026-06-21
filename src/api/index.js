import axios from 'axios'

// baseURL 统一前缀 '/api'，由 vite 开发代理 '/api/*' 转发到后端 FastAPI 服务；
// 前端请求使用 '/xxx' 路径（例如 axios.post('/upload', ...)）会拼接为 '/api/xxx'；
// vite.config.js 中 proxy 规则会将 '/api/*' → 'http://localhost:8000/*'（rewrite 去掉 /api 前缀）；
// 实际路由在 FastAPI 中定义，前端无需感知后端端口。开发环境 proxy 配置见 vite.config.js
const apiBaseUrl = '/api'

// 创建axios实例
const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 60000, // 请求超时时间
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 添加token到请求头
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    // 统一错误处理
    console.error('API Error:', error)
    // 如果是401，清除token
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
    return Promise.reject(error)
  }
)

export default api
