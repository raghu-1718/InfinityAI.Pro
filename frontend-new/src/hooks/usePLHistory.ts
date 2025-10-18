import { useQuery } from '@tanstack/react-query'
import { ENGINE_A_URL } from '../utils/constants'

export interface PLHistoryPoint {
  timestamp: string
  equity: number
  pnl: number
  pnl_pct: number
}

export interface PLHistoryResponse {
  status: string
  days: number
  series: PLHistoryPoint[]
}

export const usePLHistory = (days: number = 7) => {
  return useQuery<PLHistoryResponse>({
    queryKey: ['pl-history', days],
    queryFn: async () => {
      const qs = new URLSearchParams()
      if (days) qs.set('days', String(days))
      const res = await fetch(`${ENGINE_A_URL}/api/dhan/pl/history?${qs.toString()}`)
      if (!res.ok) throw new Error('Failed to fetch P/L history')
      return res.json()
    },
    staleTime: 30_000,
    refetchInterval: 60_000,
  })
}
