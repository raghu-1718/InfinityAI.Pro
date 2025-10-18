import axios from 'axios'
import { useState } from 'react'
import { useAuthStore } from '../store/authStore'
import { useTradeStore } from '../store/tradeStore'

const ENGINE_C_URL = import.meta.env.VITE_ENGINE_C_URL

export const useTradeExecution = () => {
  const [log, setLog] = useState<string[]>([])
  const [status, setStatus] = useState<'idle' | 'running' | 'stopping' | 'error'>('idle')
  const { getAuthHeader, ensureTokenValid } = useAuthStore()
  const { setExecuting, setActiveStrategy, addTrade } = useTradeStore()

  const startExecution = async (strategy: string, capital: number) => {
    try {
      await ensureTokenValid()
      setStatus('running')
      setExecuting(true)
      setActiveStrategy(strategy)
      setLog((prev) => [...prev, `▶ Starting strategy "${strategy}" with ₹${capital.toLocaleString()}`])
      
      const res = await axios.post(
        `${ENGINE_C_URL}/api/execute/start`,
        { strategy, capital },
        { headers: getAuthHeader() }
      )
      
      setLog((prev) => [...prev, `✅ ${res.data.message || 'Execution started successfully'}`])
      
      // Add initial trade log
      addTrade({
        id: `trade_${Date.now()}`,
        timestamp: new Date().toISOString(),
        symbol: strategy,
        type: 'BUY',
        quantity: 0,
        price: capital,
        status: 'pending',
        strategy,
      })
    } catch (e: any) {
      setStatus('error')
      setExecuting(false)
      setLog((prev) => [...prev, `❌ Error: ${e.response?.data?.message || e.message}`])
    }
  }

  const stopExecution = async () => {
    try {
      await ensureTokenValid()
      setStatus('stopping')
      
      const res = await axios.post(
        `${ENGINE_C_URL}/api/execute/stop`,
        {},
        { headers: getAuthHeader() }
      )
      
      setLog((prev) => [...prev, `🛑 ${res.data.message || 'Execution stopped'}`])
      setStatus('idle')
      setExecuting(false)
      setActiveStrategy(null)
    } catch (e: any) {
      setLog((prev) => [...prev, `❌ Error stopping: ${e.response?.data?.message || e.message}`])
      setStatus('error')
    }
  }

  const clearLog = () => {
    setLog([])
  }

  return { 
    status, 
    log, 
    startExecution, 
    stopExecution,
    clearLog 
  }
}
