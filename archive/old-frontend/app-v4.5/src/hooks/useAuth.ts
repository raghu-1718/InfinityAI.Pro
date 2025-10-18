import { useEffect } from 'react'
import { useAuthStore } from '../store/authStore'

export function useAuth() {
  const token = useAuthStore(s => s.token)
  const setToken = useAuthStore(s => s.setToken)

  useEffect(() => {
    // Placeholder: in production, fetch token via OAuth or session API
    if (!token) {
      const t = sessionStorage.getItem('iaip_token')
      if (t) setToken(t)
    }
  }, [token, setToken])

  return { token, setToken }
}
