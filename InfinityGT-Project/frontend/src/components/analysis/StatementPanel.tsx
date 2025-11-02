import { useState } from 'react'
import { useDhanStatement, StatementRow } from '../../hooks/useDhanStatement'
import { ENGINE_A_URL } from '../../utils/constants'
import { Download } from 'lucide-react'

export default function StatementPanel() {
  const [page, setPage] = useState(1)
  const [symbol, setSymbol] = useState('')
  const [side, setSide] = useState('')
  const [status, setStatus] = useState('')
  
  const { data, isLoading, error } = useDhanStatement({ page, pageSize: 20, symbol, side, status })

  const exportCSV = () => {
    const qs = new URLSearchParams({ page: String(page), page_size: '1000', symbol, side, status })
    window.open(`${ENGINE_A_URL}/api/dhan/statement.csv?${qs.toString()}`, '_blank')
  }

  const exportPDF = () => {
    const qs = new URLSearchParams({ page: String(page), page_size: '1000', symbol, side, status })
    window.open(`${ENGINE_A_URL}/api/dhan/statement.pdf?${qs.toString()}`, '_blank')
  }

  return (
    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white font-semibold">Account Statement</h3>
        <div className="flex gap-2">
          <button onClick={exportCSV} className="px-3 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-500 flex items-center gap-2">
            <Download size={16} /> CSV
          </button>
          <button onClick={exportPDF} className="px-3 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-500 flex items-center gap-2">
            <Download size={16} /> PDF
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <input
          type="text"
          className="bg-gray-900 text-white text-sm px-3 py-2 rounded-lg border border-gray-700"
          placeholder="Symbol (e.g., INFY)"
          value={symbol}
          onChange={(e) => { setSymbol(e.target.value); setPage(1); }}
        />
        <select
          className="bg-gray-900 text-white text-sm px-3 py-2 rounded-lg border border-gray-700"
          value={side}
          onChange={(e) => { setSide(e.target.value); setPage(1); }}
        >
          <option value="">All Sides</option>
          <option value="BUY">BUY</option>
          <option value="SELL">SELL</option>
        </select>
        <select
          className="bg-gray-900 text-white text-sm px-3 py-2 rounded-lg border border-gray-700"
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
        >
          <option value="">All Status</option>
          <option value="PENDING">PENDING</option>
          <option value="COMPLETED">COMPLETED</option>
          <option value="REJECTED">REJECTED</option>
        </select>
      </div>

      {isLoading && <p className="text-gray-400">Loading statement...</p>}
      {error && <p className="text-red-400">Failed to load statement.</p>}
      {!isLoading && !error && (
        <>
          <div className="overflow-x-auto mb-4">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 text-left">
                  <th className="py-2">Time</th>
                  <th className="py-2">Order ID</th>
                  <th className="py-2">Symbol</th>
                  <th className="py-2">Side</th>
                  <th className="py-2">Qty</th>
                  <th className="py-2">Price</th>
                  <th className="py-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {(data?.rows || []).map((r: StatementRow, idx: number) => (
                  <tr key={idx}>
                    <td className="py-2 text-gray-400">{r.time || '-'}</td>
                    <td className="py-2 text-gray-300">{r.orderId || '-'}</td>
                    <td className="py-2 text-white">{r.symbol || '-'}</td>
                    <td className="py-2 text-gray-300">{r.side || '-'}</td>
                    <td className="py-2 text-gray-300">{r.qty ?? '-'}</td>
                    <td className="py-2 text-gray-300">{r.price != null ? `₹${r.price}` : '-'}</td>
                    <td className="py-2 text-gray-300">{r.status || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-sm">
            <p className="text-gray-400">
              Page {data?.page || 1} of {data?.total_pages || 1} ({data?.total || 0} total)
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page <= 1}
                className="px-3 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(Math.min(data?.total_pages || 1, page + 1))}
                disabled={page >= (data?.total_pages || 1)}
                className="px-3 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
