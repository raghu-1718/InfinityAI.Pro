import { useWebSocketFeed } from '../../hooks/useWebSocketFeed'
import { useEngineHealth } from '../../hooks/useEngineHealth'
import { Activity, Zap } from 'lucide-react'

export default function LiveEngineGrid() {
  useWebSocketFeed() // Auto-refresh via Engine D WebSocket
  const { data: engines, isLoading } = useEngineHealth()

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="p-6 rounded-xl bg-gray-800 animate-pulse">
            <div className="h-24 bg-gray-700 rounded"></div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      {engines?.map((engine) => (
        <div
          key={engine.key}
          className={`p-6 rounded-xl bg-gray-800 border-2 transition-all duration-300 hover:shadow-xl ${
            engine.healthy
              ? 'border-green-500 hover:border-green-400'
              : 'border-red-600 hover:border-red-500'
          }`}
        >
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center gap-3">
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  engine.healthy ? 'bg-green-600' : 'bg-red-600'
                }`}
              >
                <span className="text-white font-bold text-lg">{engine.key}</span>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">
                  Engine {engine.key}
                </h3>
                <p className="text-sm text-gray-400">{engine.service}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {engine.healthy ? (
                <Activity className="text-green-400 animate-pulse" size={20} />
              ) : (
                <Zap className="text-red-400" size={20} />
              )}
              <span
                className={`w-3 h-3 rounded-full ${
                  engine.healthy ? 'bg-green-400 animate-pulse' : 'bg-red-400'
                }`}
              ></span>
            </div>
          </div>
          
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Status:</span>
              <span className={`font-semibold ${engine.healthy ? 'text-green-400' : 'text-red-400'}`}>
                {engine.status}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Response Time:</span>
              <span className="text-white font-mono">
                {engine.response_time_ms || '--'} ms
              </span>
            </div>
            {engine.error && (
              <div className="mt-2 p-2 bg-red-900/20 border border-red-800 rounded text-red-400 text-xs">
                {engine.error}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
