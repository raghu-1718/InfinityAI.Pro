import { useQuery } from '@tanstack/react-query'
import { ENGINE_A_URL } from '../utils/constants'

export const useExchanges = () => {
  return useQuery({
    queryKey: ['exchanges'],
    queryFn: async () => {
      const res = await fetch(`${ENGINE_A_URL}/api/exchanges`)
      if (!res.ok) throw new Error('Failed to fetch exchanges')
      return res.json()
    },
    staleTime: 600000,
  })
}
