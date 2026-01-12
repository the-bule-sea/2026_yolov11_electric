import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import router from '@/router'

const service = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers['Authorization'] = `Bearer ${userStore.token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    const res = response.data
    // 如果是二进制流（图片），直接返回
    if (response.config.responseType === 'blob') {
      return response
    }
    // 正常 JSON
    if (res.code === 200) {
      return res
    } else {
      ElMessage.error(res.msg || '请求失败')
      return Promise.reject(new Error(res.msg || 'Error'))
    }
  },
  error => {
    if (error.response && error.response.status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      router.push('/login')
      ElMessage.error('登录过期，请重新登录')
    } else {
      ElMessage.error(error.message || '连接服务器失败')
    }
    return Promise.reject(error)
  }
)

export default service
