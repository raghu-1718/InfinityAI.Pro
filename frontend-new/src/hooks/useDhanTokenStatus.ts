import { useQuery } from '@tanstack/react-query'
import { ENGINE_C_URL } from '../utils/constants'

interface TokenStatus {
  client_id: string
  has_token: boolean
  exp: number
  seconds_remaining: number
  is_fresh: boolean
  checked_at_utc: string
}

interface TokenFreshness {
  ok: boolean
  exp: number
  target_utc: number
  message: string
  checked_at_utc: string
}

export const useDhanTokenStatus = () => {
  return useQuery<TokenStatus>({
    queryKey: ['dhan-token-status'],
    queryFn: async () => {
      const response = await fetch(`${ENGINE_C_URL}/api/dhan/token/status`)
      if (!response.ok) throw new Error('Failed to fetch token status')
      return response.json()
    },
    refetchInterval: 60000, // Refresh every minute
    staleTime: 30000
  })
}

export const useDhanTokenFreshness = () => {
  return useQuery<TokenFreshness>({
    queryKey: ['dhan-token-freshness'],
    queryFn: async () => {
      const response = await fetch(
        `${ENGINE_C_URL}/api/dhan/token/validate-freshness?market_open_ist=09:15&buffer_minutes=15`
      )
      if (!response.ok) throw new Error('Failed to validate token freshness')
      return response.json()
    },
    refetchInterval: 300000, // Refresh every 5 minutes
    staleTime: 120000
  })
}
