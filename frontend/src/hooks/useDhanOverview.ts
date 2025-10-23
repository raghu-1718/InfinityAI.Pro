import { useQuery } from '@tanstack/react-query'
import { ENGINE_A_URL } from '../utils/constants'

export const useDhanOverview = () => {
  return useQuery({
    queryKey: ['dhan-overview'],
    queryFn: async () => {
      const res = await fetch(`${ENGINE_A_URL}/api/dhan/overview`)
      if (!res.ok) throw new Error('Failed to fetch Dhan overview')
      return res.json()
    },
    refetchInterval: 30000,
    staleTime: 15000,
  })
}
