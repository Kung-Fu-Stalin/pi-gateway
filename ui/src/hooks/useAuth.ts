import { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import axios from 'axios'
import { useAuthStore } from '../store/auth'

export function useAuth() {
  const [loading, setLoading] = useState(true)
  const { setAccessToken, setUser, accessToken } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    if (accessToken) {
      setLoading(false)
      return
    }

    axios.post('/api/auth/refresh', {}, { withCredentials: true })
      .then(res => {
        setAccessToken(res.data.access_token)
        return axios.get('/api/auth/me', {
          headers: { Authorization: `Bearer ${res.data.access_token}` },
          withCredentials: true,
        })
      })
      .then(res => setUser(res.data))
      .catch(() => {
        if (location.pathname !== '/login') navigate('/login')
      })
      .finally(() => setLoading(false))
  }, [])

  return { loading }
}