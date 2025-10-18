import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const ENGINES = {
  A: import.meta.env.VITE_ENGINE_A_URL,
  B: import.meta.env.VITE_ENGINE_B_URL,
  C: import.meta.env.VITE_ENGINE_C_URL,
  D: import.meta.env.VITE_ENGINE_D_URL,
}

interface EngineHealth {
  key: string
  status: string
  healthy?: boolean
  response_time_ms?: number
  service?: string
  error?: string
}

export function useEngineHealth() {
  return useQuery<EngineHealth[]>({
    queryKey: ['engine-health'],
    queryFn: async () => {
      const results = await Promise.all(
        Object.entries(ENGINES).map(async ([key, url]) => {
          const startTime = Date.now()
          try {
            const res = await axios.get(`${url}/health`, { 
              timeout: 5000,
              headers: { 'Accept': 'application/json' }
            })
            const responseTime = Date.now() - startTime
            
            return {
              key,
              status: res.data.status || 'healthy',
              healthy: true,
              response_time_ms: responseTime,
              service: res.data.service || `engine-${key.toLowerCase()}`,
              ...res.data,
            }
          } catch (err: any) {
            const responseTime = Date.now() - startTime
            return {
              key,
              status: 'offline',
              healthy: false,
              response_time_ms: responseTime,
              error: err.message || 'Connection failed',
            }
          }
        })
      )
      return results
    },
    refetchInterval: parseInt(import.meta.env.VITE_REFRESH_INTERVAL || '5000'),
    staleTime: 3000,
  })
}
