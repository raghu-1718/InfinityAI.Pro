import { Shield, Clock, AlertCircle, CheckCircle } from 'lucide-react'
import { useDhanTokenStatus, useDhanTokenFreshness } from '../../hooks/useDhanTokenStatus'

export default function TokenStatusCard() {
  const { data: status, isLoading: loadingStatus } = useDhanTokenStatus()
  const { data: freshness, isLoading: loadingFreshness } = useDhanTokenFreshness()

  const formatTimeRemaining = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (hours > 24) {
      const days = Math.floor(hours / 24)
      return `${days}d ${hours % 24}h`
    }
    return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`
  }

  if (loadingStatus || loadingFreshness) {
    return (
      <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="text-blue-400" size={20} />
          <h3 className="text-lg font-semibold text-white">Token Status</h3>
        </div>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-700 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-700 rounded w-1/2"></div>
        </div>
      </div>
    )
  }

  const isFresh = status?.is_fresh ?? false
  const isValid = freshness?.ok ?? false
  const timeRemaining = status?.seconds_remaining ?? 0

  return (
    <div className={`bg-gray-800 p-6 rounded-xl border transition-all duration-300 ${
      isFresh && isValid ? 'border-green-600' : 'border-yellow-600'
    }`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Shield className={isFresh ? "text-green-400" : "text-yellow-400"} size={20} />
          <h3 className="text-lg font-semibold text-white">Dhan Token Status</h3>
        </div>
        {isFresh && isValid ? (
          <CheckCircle className="text-green-400" size={18} />
        ) : (
          <AlertCircle className="text-yellow-400" size={18} />
        )}
      </div>

      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-gray-400 text-sm">Client ID</span>
          <span className="text-white font-mono text-sm">{status?.client_id || '--'}</span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-400 text-sm">Token Active</span>
          <span className={`font-semibold text-sm ${status?.has_token ? 'text-green-400' : 'text-red-400'}`}>
            {status?.has_token ? 'Yes' : 'No'}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <div className="flex items-center gap-1">
            <Clock className="text-gray-400" size={14} />
            <span className="text-gray-400 text-sm">Time Remaining</span>
          </div>
          <span className={`font-semibold text-sm ${timeRemaining > 7200 ? 'text-green-400' : 'text-yellow-400'}`}>
            {formatTimeRemaining(timeRemaining)}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-400 text-sm">Market Open Ready</span>
          <span className={`font-semibold text-sm ${isValid ? 'text-green-400' : 'text-yellow-400'}`}>
            {isValid ? '✓ Valid' : '⚠ Check Required'}
          </span>
        </div>

        {freshness?.message && (
          <div className="mt-3 pt-3 border-t border-gray-700">
            <p className={`text-xs ${isValid ? 'text-gray-400' : 'text-yellow-400'}`}>
              {freshness.message}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

