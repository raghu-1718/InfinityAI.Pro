/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_ENGINE_A_URL: string
  readonly VITE_ENGINE_B_URL: string
  readonly VITE_ENGINE_C_URL: string
  readonly VITE_ENGINE_D_URL: string
  readonly VITE_APP_NAME: string
  readonly VITE_REFRESH_INTERVAL: string
  readonly VITE_WS_RECONNECT_INTERVAL: string
  readonly VITE_GCP_PROJECT_ID: string
  readonly VITE_GCP_REGION: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
