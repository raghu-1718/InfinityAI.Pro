import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const ENGINE_C_URL = import.meta.env.VITE_ENGINE_C_URL as string

interface Strategy {
  name: string
  description: string
  status: string
}

export function useStrategies() {
  const { getAuthHeader, ensureTokenValid } = useAuthStore()
  return useQuery<Strategy[]>({
    queryKey: ['strategies'],
    queryFn: async () => {
      await ensureTokenValid()
      const res = await axios.get(`${ENGINE_C_URL}/api/strategies`, {
        headers: getAuthHeader(),
        timeout: 8000,
      })
      return res.data.strategies
    },
    refetchInterval: parseInt(import.meta.env.VITE_REFRESH_INTERVAL || '5000'),
    staleTime: 3000,
  })
}
