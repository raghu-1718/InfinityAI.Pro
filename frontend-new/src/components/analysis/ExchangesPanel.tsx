import { useState } from 'react'
import { useExchanges } from '../../hooks/useExchanges'
import { ENGINE_A_URL } from '../../utils/constants'

export default function ExchangesPanel() {
  const { data, isLoading, error } = useExchanges()
  const [indexSymbol, setIndexSymbol] = useState('NIFTY')
  const [ai, setAi] = useState<any>(null)
  const [loadingAI, setLoadingAI] = useState(false)

  const runAI = async () => {
    setLoadingAI(true)
    try {
      const res = await fetch(`${ENGINE_A_URL}/api/optionchain/ai/${encodeURIComponent(indexSymbol)}`)
      const j = await res.json()
      setAi(j)
    } finally {
      setLoadingAI(false)
    }
  }

  return (
    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white font-semibold">Indian Exchanges</h3>
      </div>
      {isLoading && <p className="text-gray-400">Loading exchanges...</p>}
      {error && <p className="text-red-400">Failed to load exchanges</p>}
      {!isLoading && !error && (
        <ul className="divide-y divide-gray-700 mb-4">
          {(data?.exchanges || []).map((ex: any) => (
            <li key={ex.code} className="py-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white font-medium">{ex.name}</p>
                  <p className="text-gray-500 text-xs">{ex.code} • {ex.segments.join(', ')}</p>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-4 pt-4 border-t border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <input
            className="bg-gray-900 text-white text-sm px-3 py-2 rounded-lg border border-gray-700"
            value={indexSymbol}
            onChange={(e) => setIndexSymbol(e.target.value.toUpperCase())}
            placeholder="Index (e.g., NIFTY, BANKNIFTY)"
          />
          <button
            onClick={runAI}
            className="px-3 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-500"
            disabled={loadingAI}
          >
            {loadingAI ? 'Analyzing…' : 'Analyze Option Chain (AI)'}
          </button>
        </div>
        {ai && (
          <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700">
            <p className="text-white font-semibold mb-2">Best Strategy: {ai.analysis?.strategy}</p>
            <p className="text-gray-400 text-sm mb-2">{ai.analysis?.rationale}</p>
            <ul className="text-gray-300 text-sm list-disc ml-5">
              {(ai.analysis?.legs || []).map((leg: any, idx: number) => (
                <li key={idx}>{leg.type} • {leg.strike} • {leg.expiry}</li>
              ))}
            </ul>
            {ai.analysis?.risk_reward && (
              <div className="text-xs text-gray-400 mt-2">
                <p>Max Loss: {ai.analysis.risk_reward.max_loss}</p>
                <p>Max Profit: {ai.analysis.risk_reward.max_profit}</p>
                <p>Probability: {ai.analysis.risk_reward.probability}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
