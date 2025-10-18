export const ENGINE_A_URL = import.meta.env.VITE_ENGINE_A_URL;
export const ENGINE_B_URL = import.meta.env.VITE_ENGINE_B_URL;
export const ENGINE_C_URL = import.meta.env.VITE_ENGINE_C_URL;
export const ENGINE_D_URL = import.meta.env.VITE_ENGINE_D_URL;

export const WS_DASHBOARD_URL = ENGINE_D_URL.replace('https://', 'wss://') + '/ws/dashboard';
export const AUTH_HEADER = (token?: string) => (token ? { Authorization: `Bearer ${token}` } : {});
