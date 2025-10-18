import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { API, APP } from '../utils/constants'
import { useAuthStore } from '../store/authStore'

export function useAIAnalysis() {
  const getAuthHeader = useAuthStore(s => s.getAuthHeader)
  return useQuery({
    queryKey: ['ai-signals'],
    queryFn: async () => {
      const res = await axios.get(API.analysisSignals, { headers: { ...getAuthHeader() }})
      return res.data
    },
    refetchInterval: APP.refreshMs,
  })
}
