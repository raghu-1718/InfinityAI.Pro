import { usePLHistory } from '../../hooks/usePLHistory'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { useState } from 'react'

export default function PLHistoryChart() {
  const [days, setDays] = useState(14)
  const { data, isLoading, error } = usePLHistory(days)

  const series = data?.series ?? []

  return (
    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-white font-semibold">P/L History</h2>
        <div className="flex items-center gap-2 text-sm">
          <label htmlFor="pl-days" className="text-gray-400">Days</label>
          <select id="pl-days"
            className="bg-gray-900 text-gray-200 border border-gray-700 rounded px-2 py-1"
            value={days}
            onChange={(e) => setDays(parseInt(e.target.value, 10))}
          >
            {[7, 14, 30, 60, 90].map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>
      </div>

      {isLoading && <p className="text-gray-400">Loading...</p>}
      {error && <p className="text-red-400">Failed to load P/L history.</p>}

      {!isLoading && !error && series.length > 0 && (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={series} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="timestamp" tick={{ fill: '#9CA3AF' }} hide/>
              <YAxis tick={{ fill: '#9CA3AF' }} domain={["auto", "auto"]}/>
              <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151' }} />
              <Line type="monotone" dataKey="equity" stroke="#60A5FA" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="pnl" stroke="#34D399" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {!isLoading && !error && series.length === 0 && (
        <p className="text-gray-400">No data available.</p>
      )}
    </div>
  )
}
