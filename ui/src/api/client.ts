import axios from 'axios'
import { useAuthStore } from '../store/auth'
import { useToast } from '../components/Toast'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      try {
        const res = await axios.post('/api/auth/refresh', {}, { withCredentials: true })
        const newToken = res.data.access_token
        useAuthStore.getState().setAccessToken(newToken)
        original.headers.Authorization = `Bearer ${newToken}`
        return api(original)
      } catch {
        useAuthStore.getState().logout()
        window.location.href = '/login'
      }
    }

    if (error.response?.status !== 401) {
      const detail = error.response?.data?.detail
      let message: string

      if (typeof detail === 'string') {
        message = detail
      } else if (Array.isArray(detail)) {
        message = detail.map((e: { msg: string }) => e.msg).join(', ')
      } else {
        message = error.message || 'Something went wrong'
      }

      useToast.getState().add(message)
    }

    return Promise.reject(error)
  }
)

export default api