import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import { ENDPOINTS, WS_RECONNECT_INTERVAL } from '../utils/constants'

export const useWebSocketFeed = () => {
  const wsRef = useRef<WebSocket | null>(null)
  const queryClient = useQueryClient()
  const { getAuthHeader, ensureTokenValid } = useAuthStore()
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const connectWebSocket = async () => {
      try {
        await ensureTokenValid()
  // const token = getAuthHeader().Authorization?.split(' ')[1]
        
        // For now, we'll use a simple connection without token validation
        // In production, Engine D would validate the token
  const ws = new WebSocket(ENDPOINTS.engineD.wsDashboard)
        wsRef.current = ws

        ws.onopen = () => {
          console.log('✅ WebSocket connected to Engine D')
        }

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data)
            console.log('📨 WS Message:', msg)
            
            // Invalidate queries based on message type
            if (msg.type === 'dhan_update' || msg.type === 'engine_health' || msg.type === 'trade_update') {
              queryClient.invalidateQueries({ queryKey: ['engine-health'] })
              queryClient.invalidateQueries({ queryKey: ['ai-analysis'] })
                queryClient.invalidateQueries({ queryKey: ['dhan-overview'] })
                queryClient.invalidateQueries({ queryKey: ['dhan-statement'] })
                queryClient.invalidateQueries({ queryKey: ['pl-history'] })
            }
          } catch (e) {
            console.error('WS parse error:', e)
          }
        }

        ws.onclose = () => {
          console.warn('⚠️ WebSocket disconnected')
          // Reconnect after delay
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, WS_RECONNECT_INTERVAL)
        }

        ws.onerror = (e) => {
          console.error('WS Error:', e)
        }
      } catch (error) {
        console.error('WebSocket connection failed:', error)
        // Retry connection
  reconnectTimeoutRef.current = setTimeout(connectWebSocket, WS_RECONNECT_INTERVAL)
      }
    }

    connectWebSocket()

    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [queryClient, ensureTokenValid, getAuthHeader])

  return wsRef
}
