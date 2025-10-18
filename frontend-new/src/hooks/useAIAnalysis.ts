import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const ENGINE_B_URL = import.meta.env.VITE_ENGINE_B_URL as string

interface AISignal {
  symbol: string
  direction: 'BUY' | 'SELL' | 'HOLD'
  score: number
  timestamp: string
}

interface AIAnalysisResponse {
  signals: AISignal[]
  [key: string]: any
}

export function useAIAnalysis() {
  return useQuery<AIAnalysisResponse>({
    queryKey: ['ai-analysis'],
    queryFn: async () => {
      const res = await axios.get(`${ENGINE_B_URL}/api/ai-signals`, {
        timeout: 8000,
        headers: { 'Accept': 'application/json' },
      })
      return res.data
    },
    refetchInterval: parseInt(import.meta.env.VITE_REFRESH_INTERVAL || '5000'),
    staleTime: 3000,
  })
}
