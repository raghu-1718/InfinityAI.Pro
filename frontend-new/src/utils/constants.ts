export const ENGINE_A_URL = import.meta.env.VITE_ENGINE_A_URL as string
export const ENGINE_B_URL = import.meta.env.VITE_ENGINE_B_URL as string
export const ENGINE_C_URL = import.meta.env.VITE_ENGINE_C_URL as string
export const ENGINE_D_URL = import.meta.env.VITE_ENGINE_D_URL as string

export const WS_RECONNECT_INTERVAL = parseInt(
  import.meta.env.VITE_WS_RECONNECT_INTERVAL || '3000',
  10
)

export const ENDPOINTS = {
  engineA: {
    baseUrl: ENGINE_A_URL,
  },
  engineB: {
    baseUrl: ENGINE_B_URL,
  },
  engineC: {
    baseUrl: ENGINE_C_URL,
  },
  engineD: {
    baseUrl: ENGINE_D_URL,
    wsDashboard: (ENGINE_D_URL || '').replace('https://', 'wss://') + '/ws/dashboard',
  },
}
