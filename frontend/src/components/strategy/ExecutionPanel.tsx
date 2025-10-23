import { useState } from 'react'
import { useTradeExecution } from '../../hooks/useTradeExecution'

export default function ExecutionPanel() {
  const { status, log, startExecution, stopExecution, clearLog } = useTradeExecution()
  const [strategy, setStrategy] = useState('NIFTY-BREAKOUT')
  const [capital, setCapital] = useState(100000)

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
      <div className="flex flex-col md:flex-row md:items-end gap-4 mb-6">
        <div className="flex-1">
          <label className="block text-sm text-gray-400 mb-1">Strategy</label>
          <input
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
            className="w-full bg-gray-800 text-white p-3 rounded border border-gray-700"
            placeholder="Strategy name"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Capital (₹)</label>
          <input
            type="number"
            value={capital}
            onChange={(e) => setCapital(parseInt(e.target.value || '0', 10))}
            className="w-40 bg-gray-800 text-white p-3 rounded border border-gray-700"
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => startExecution(strategy, capital)}
            disabled={status === 'running'}
            className="bg-green-600 hover:bg-green-500 text-white px-4 py-3 rounded disabled:bg-gray-700"
          >Start</button>
          <button
            onClick={stopExecution}
            disabled={status !== 'running'}
            className="bg-red-600 hover:bg-red-500 text-white px-4 py-3 rounded disabled:bg-gray-700"
          >Stop</button>
          <button
            onClick={clearLog}
            className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-3 rounded"
          >Clear Log</button>
        </div>
      </div>

      <div className="bg-black/30 rounded p-4 h-64 overflow-auto border border-gray-800 text-sm text-gray-200 font-mono">
        {log.length === 0 ? (
          <p className="text-gray-500">No execution logs yet.</p>
        ) : (
          log.map((l, i) => <div key={i}>{l}</div>)
        )}
      </div>
    </div>
  )
}
