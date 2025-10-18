import { useQuery } from '@tanstack/react-query'
import { ENGINE_A_URL } from '../utils/constants'

export interface StatementRow {
  orderId?: string
  symbol?: string
  side?: string
  qty?: number
  price?: number
  status?: string
  time?: string
}

export interface StatementResponse {
  source: string
  rows: StatementRow[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface StatementFilters {
  page?: number
  pageSize?: number
  symbol?: string
  side?: string
  status?: string
  from?: string
  to?: string
}

export const useDhanStatement = (filters: StatementFilters = {}) => {
  const { page = 1, pageSize = 20, symbol, side, status, from, to } = filters
  return useQuery<StatementResponse>({
    queryKey: ['dhan-statement', { page, pageSize, symbol, side, status, from, to }],
    queryFn: async () => {
      const qs = new URLSearchParams()
      qs.set('page', String(page))
      qs.set('page_size', String(pageSize))
      if (symbol) qs.set('symbol', symbol)
      if (side) qs.set('side', side)
      if (status) qs.set('status', status)
      if (from) qs.set('from', from)
      if (to) qs.set('to', to)
      const res = await fetch(`${ENGINE_A_URL}/api/dhan/statement?${qs.toString()}`)
      if (!res.ok) throw new Error('Failed to fetch Dhan statement')
      return res.json()
    },
      placeholderData: (previousData) => previousData,
    staleTime: 30000,
    refetchInterval: 60000,
  })
}
