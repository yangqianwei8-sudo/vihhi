import axios from 'axios'

// 获取 API base URL
const getBaseURL = () => {
  // 如果设置了环境变量，使用环境变量
  if (process.env.VUE_APP_API_BASE_URL) {
    return process.env.VUE_APP_API_BASE_URL
  }
  // 生产环境使用相对路径
  if (process.env.NODE_ENV === 'production') {
    return '/api'
  }
  // 开发环境使用 localhost
  return 'http://localhost:8001/api'
}

// 创建 axios 实例
const api = axios.create({
  baseURL: getBaseURL(),
  timeout: 15000, // 增加超时时间到15秒
  withCredentials: true, // 支持 cookie/session
  headers: {
    'Content-Type': 'application/json'
  },
  // 添加重试配置
  validateStatus: function (status) {
    return status >= 200 && status < 500 // 不抛出错误，让响应拦截器处理
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 从 localStorage 获取 token（如果有）
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
    // 处理网络错误（无法连接到服务器）
    if (error.code === 'ECONNABORTED' || error.message === 'Network Error' || !error.response) {
      console.error('API请求失败:', error.message)
      const errorMsg = error.code === 'ECONNABORTED' 
        ? '请求超时，请检查网络连接或稍后重试' 
        : '无法连接到服务器，请确保后端服务已启动（端口8001）'
      return Promise.reject({
        message: errorMsg,
        code: error.code || 'NETWORK_ERROR',
        originalError: error
      })
    }
    
    if (error.response) {
      // 服务器返回了错误状态码
      if (error.response.status === 401) {
        // 未授权，清除 token 并跳转到登录页
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
      return Promise.reject(error.response.data || error.message)
    }
    return Promise.reject(error.message || '网络错误')
  }
)

export default api

