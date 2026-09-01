import axios from 'axios'

const BASE_URL = 'http://127.0.0.1:8001/api/v1'

const instance = axios.create({
  baseURL: BASE_URL,
  timeout: 5000
})

// 请求拦截器
instance.interceptors.request.use(
  (config) => {
      const token= localStorage.getItem('token')
    // 每次请求需要带上token
      if (token) {
    config.headers.Authorization = `Bearer ${token}`
      }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
instance.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    //可以加后端数据异常传的code码进行报错提示
    return Promise.reject(error)
  }
)

export default instance
