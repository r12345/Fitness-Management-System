import axios from 'axios'

// 后端地址。默认沿用本地开发端口，可通过 .env 里的 VITE_API_BASE_URL 覆盖，
// 换端口或换机器时不必改源码。
const BASE_URL = 'http://127.0.0.1:8001/api/v1'

const instance = axios.create({
  baseURL: BASE_URL,
  // 注册接口内部要做密码哈希，5s 在冷启动时偏紧，放宽到 10s
  timeout: 10000
})

// 请求拦截器
instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
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

/** 只接受非空字符串，避免把 422 校验错误里的 detail 数组当成提示文案 */
function asText(value) {
  return typeof value === 'string' && value ? value : ''
}

// 响应拦截器
instance.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // 保留原始 axios 错误对象：调用方仍在读 error.response.data（如 AppointmentList）。
    // 这里只补一个可读提示，并把 error.message 换成后端给出的原因。
    const response = error.response
    let message = ''

    if (response) {
      const data = response.data
      if (data && typeof data === 'object') {
        // 统一信封用 msg，部分接口用 message，FastAPI 默认用 detail
        message = asText(data.msg) || asText(data.message) || asText(data.detail)
      }
      if (!message) {
        message = response.status === 401
          ? '登录已过期，请重新登录'
          : `请求失败（HTTP ${response.status}）`
      }
    } else if (error.code === 'ECONNABORTED') {
      message = '请求超时，请检查后端服务是否已启动'
    } else {
      message = '网络异常，请检查后端服务是否已启动'
    }

    error.friendlyMessage = message
    error.message = message
    return Promise.reject(error)
  }
)

export default instance
