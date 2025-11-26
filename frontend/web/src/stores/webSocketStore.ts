import { create } from 'zustand';
import { useAppStore } from './appStore';

interface WebSocketState {
  socket: WebSocket | null;
  isConnected: boolean;
  reconnectAttempts: number;
  maxReconnectAttempts: number;
  reconnectDelay: number;

  connect: () => void;
  disconnect: () => void;
  sendMessage: (message: any) => void;
  subscribe: (channel: string) => void;
  unsubscribe: (channel: string) => void;
}

// Updated to use Engine C (Execution) which now handles WebSocket aggregation
const WS_URL = 'wss://infinityai-engine-c-execution-26140490557.us-central1.run.app/ws/dashboard';

export const useWebSocketStore = create<WebSocketState>((set, get) => ({
  socket: null,
  isConnected: false,
  reconnectAttempts: 0,
  maxReconnectAttempts: 5,
  reconnectDelay: 1000,

  connect: () => {
    const { socket, isConnected, reconnectAttempts, maxReconnectAttempts } = get();

    if (socket && isConnected) {
      console.log('🔌 WebSocket already connected');
      return;
    }

    if (reconnectAttempts >= maxReconnectAttempts) {
      console.error('🚫 Max reconnection attempts reached');
      return;
    }

    try {
      console.log('🔌 Connecting to WebSocket...');
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        set({ socket: ws, isConnected: true, reconnectAttempts: 0 });
        useAppStore.getState().setWebSocketStatus(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 WebSocket message:', data);

          // Update app store with real-time data
          if (data.type === 'market_data') {
            useAppStore.getState().setRealTimeData(data.payload);
          } else if (data.type === 'engine_status') {
            useAppStore.getState().updateEngineStatus(data.engine, data.status);
          } else if (data.type === 'ai_analysis') {
            useAppStore.getState().setAiAnalysis(data.analysisType, data.analysis);
          }
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        set({ socket: null, isConnected: false });
        useAppStore.getState().setWebSocketStatus(false);

        // Auto-reconnect with exponential backoff
        const attempts = get().reconnectAttempts;
        if (attempts < maxReconnectAttempts) {
          setTimeout(() => {
            set({ reconnectAttempts: attempts + 1 });
            get().connect();
          }, get().reconnectDelay * Math.pow(2, attempts));
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        set({ socket: null, isConnected: false });
        useAppStore.getState().setWebSocketStatus(false);
      };

      set({ socket: ws });
    } catch (error) {
      console.error('❌ WebSocket connection error:', error);
    }
  },

  disconnect: () => {
    const { socket } = get();
    if (socket) {
      socket.close();
      set({ socket: null, isConnected: false, reconnectAttempts: 0 });
    }
  },

  sendMessage: (message) => {
    const { socket, isConnected } = get();
    if (socket && isConnected) {
      socket.send(JSON.stringify(message));
    } else {
      console.warn('⚠️ WebSocket not connected');
    }
  },

  subscribe: (channel) => {
    get().sendMessage({ type: 'subscribe', channel });
  },

  unsubscribe: (channel) => {
    get().sendMessage({ type: 'unsubscribe', channel });
  },
}));
