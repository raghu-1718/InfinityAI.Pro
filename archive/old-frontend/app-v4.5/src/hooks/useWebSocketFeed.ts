import { useEffect, useRef } from 'react'
import { APP, WS } from '../utils/constants'
import { useAuthStore } from '../store/authStore'

export function useWebSocketFeed(onMessage: (data: any) => void) {
  const token = useAuthStore(s => s.token)
  const wsRef = useRef<WebSocket | null>(null)
  const timerRef = useRef<number | null>(null)

  useEffect(() => {
    function connect() {
      try {
        wsRef.current = new WebSocket(WS.dashboard(token || undefined))
        wsRef.current.onmessage = (ev) => {
          try { onMessage(JSON.parse(ev.data)) } catch { /* ignore */ }
        }
        wsRef.current.onclose = () => scheduleReconnect()
        wsRef.current.onerror = () => scheduleReconnect()
      } catch {
        scheduleReconnect()
      }
    }
    function scheduleReconnect() {
      if (timerRef.current) window.clearTimeout(timerRef.current)
      timerRef.current = window.setTimeout(connect, APP.wsReconnectMs)
    }
    connect()
    return () => {
      if (timerRef.current) window.clearTimeout(timerRef.current)
      wsRef.current?.close()
    }
  }, [token, onMessage])
}
