import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const ENGINE_C_URL = import.meta.env.VITE_ENGINE_C_URL as string

interface PortfolioData {
  value: number
  pnl: number
}

export function usePortfolio() {
  const { getAuthHeader, ensureTokenValid } = useAuthStore()
  return useQuery<PortfolioData>({
    queryKey: ['portfolio'],
    queryFn: async () => {
      await ensureTokenValid()
      const res = await axios.get(`${ENGINE_C_URL}/api/portfolio`, {
        headers: getAuthHeader(),
        timeout: 8000,
      })
      return res.data
    },
    refetchInterval: parseInt(import.meta.env.VITE_REFRESH_INTERVAL || '5000'),
    staleTime: 3000,
  })
}
