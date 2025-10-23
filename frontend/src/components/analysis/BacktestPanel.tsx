import { useState } from 'react'
import { ENGINE_A_URL } from '../../utils/constants'

interface BacktestResp {
  status: string
  symbol: string
  strategy: string
  metrics: { total_return_pct: number; win_rate_pct: number; max_drawdown_pct: number }
  equity_curve: { timestamp: string; equity: number }[]
}

export default function BacktestPanel() {
  const [symbol, setSymbol] = useState('NIFTY')
  const [strategy, setStrategy] = useState('bull_call_spread')
  const [days, setDays] = useState(30)
  const [data, setData] = useState<BacktestResp | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runBacktest = async () => {
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const qs = new URLSearchParams({ strategy, days: String(days) })
      const res = await fetch(`${ENGINE_A_URL}/api/optionchain/backtest/${encodeURIComponent(symbol)}?${qs.toString()}`)
      if (!res.ok) throw new Error('Failed to run backtest')
      const json: BacktestResp = await res.json()
      setData(json)
    } catch (e: any) {
      setError(e.message || 'Backtest failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
      <h2 className="text-white font-semibold mb-4">Option Strategy Backtest</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
        <div>
          <label htmlFor="bt-symbol" className="block text-gray-400 text-sm mb-1">Symbol</label>
          <input id="bt-symbol" className="w-full bg-gray-900 text-gray-200 border border-gray-700 rounded px-3 py-2" value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} />
        </div>
        <div>
          <label htmlFor="bt-strategy" className="block text-gray-400 text-sm mb-1">Strategy</label>
          <select id="bt-strategy" className="w-full bg-gray-900 text-gray-200 border border-gray-700 rounded px-3 py-2" value={strategy} onChange={(e) => setStrategy(e.target.value)}>
            <option value="bull_call_spread">Bull Call Spread</option>
            <option value="bear_put_spread">Bear Put Spread</option>
            <option value="iron_condor">Iron Condor</option>
          </select>
        </div>
        <div>
          <label htmlFor="bt-days" className="block text-gray-400 text-sm mb-1">Days</label>
          <input id="bt-days" type="number" min={5} max={180} className="w-full bg-gray-900 text-gray-200 border border-gray-700 rounded px-3 py-2" value={days} onChange={(e) => setDays(parseInt(e.target.value, 10) || 30)} />
        </div>
      </div>

      <button onClick={runBacktest} className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded" disabled={loading}>
        {loading ? 'Running…' : 'Run Backtest'}
      </button>

      {error && <p className="text-red-400 mt-3">{error}</p>}

      {data && (
        <div className="mt-4 text-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="bg-gray-900 p-3 rounded border border-gray-700">
              <p className="text-gray-400 text-sm">Total Return</p>
              <p className="text-white text-xl">{data.metrics.total_return_pct}%</p>
            </div>
            <div className="bg-gray-900 p-3 rounded border border-gray-700">
              <p className="text-gray-400 text-sm">Win Rate</p>
              <p className="text-white text-xl">{data.metrics.win_rate_pct}%</p>
            </div>
            <div className="bg-gray-900 p-3 rounded border border-gray-700">
              <p className="text-gray-400 text-sm">Max Drawdown</p>
              <p className="text-white text-xl">{data.metrics.max_drawdown_pct}%</p>
            </div>
          </div>
          <div className="mt-4 text-gray-400 text-sm">
            Equity curve points: {data.equity_curve.length}
          </div>
        </div>
      )}
    </div>
  )
}
