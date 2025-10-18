export const ENGINE_A_URL = import.meta.env.VITE_ENGINE_A_URL
export const ENGINE_B_URL = import.meta.env.VITE_ENGINE_B_URL
export const ENGINE_C_URL = import.meta.env.VITE_ENGINE_C_URL
export const ENGINE_D_URL = import.meta.env.VITE_ENGINE_D_URL

export const API = {
  analysisSignals: `${ENGINE_B_URL}/api/ai-signals`,
  tradeStart: `${ENGINE_C_URL}/api/trade/start`,
  tradeStop: `${ENGINE_C_URL}/api/trade/stop`,
  orchestratorHealth: `${ENGINE_D_URL}/api/health/simple`,
}

export const WS = {
  dashboard: (token?: string) => {
    const url = new URL(`${ENGINE_D_URL.replace('https', 'wss')}/ws/dashboard`)
    if (token) url.searchParams.set('token', token)
    return url.toString()
  }
}

export const APP = {
  name: import.meta.env.VITE_APP_NAME || 'InfinityAI.Pro',
  refreshMs: parseInt(import.meta.env.VITE_REFRESH_INTERVAL || '5000'),
  wsReconnectMs: parseInt(import.meta.env.VITE_WS_RECONNECT_INTERVAL || '3000'),
  gcpProject: import.meta.env.VITE_GCP_PROJECT_ID,
  gcpRegion: import.meta.env.VITE_GCP_REGION,
}
