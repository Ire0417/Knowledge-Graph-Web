import axios from 'axios'

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '/api').trim()

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
    // 可以在这里添加token等认证信息
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
    return Promise.reject(error)
  }
)

export default api