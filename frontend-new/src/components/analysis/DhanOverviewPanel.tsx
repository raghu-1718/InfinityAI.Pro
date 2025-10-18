import { useDhanOverview } from '../../hooks/useDhanOverview'

export default function DhanOverviewPanel() {
  const { data, isLoading, error } = useDhanOverview()

  return (
    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
      <h3 className="text-white font-semibold mb-4">Dhan Overview</h3>
      {isLoading && <p className="text-gray-400">Loading overview...</p>}
      {error && <p className="text-red-400">Failed to load overview.</p>}
      {!isLoading && !error && data && (
        <div className="space-y-4">
          {/* Funds */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-900 p-4 rounded-lg border border-gray-700">
              <p className="text-xs text-gray-400">Available Balance</p>
              <p className="text-white text-lg font-semibold">₹{data.funds?.availabelBalance?.toLocaleString?.() ?? data.funds?.availableBalance ?? 0}</p>
            </div>
            <div className="bg-gray-900 p-4 rounded-lg border border-gray-700">
              <p className="text-xs text-gray-400">Withdrawable</p>
              <p className="text-white text-lg font-semibold">₹{data.funds?.withdrawableBalance?.toLocaleString?.() ?? 0}</p>
            </div>
            <div className="bg-gray-900 p-4 rounded-lg border border-gray-700">
              <p className="text-xs text-gray-400">Net Positions</p>
              <p className="text-white text-lg font-semibold">{(data.positions || []).length}</p>
            </div>
            <div className="bg-gray-900 p-4 rounded-lg border border-gray-700">
              <p className="text-xs text-gray-400">Holdings</p>
              <p className="text-white text-lg font-semibold">{(data.holdings || []).length}</p>
            </div>
          </div>

          {/* Positions */}
          <div>
            <p className="text-white font-medium mb-2">Positions</p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 text-left">
                    <th className="py-2">Symbol</th>
                    <th className="py-2">Qty</th>
                    <th className="py-2">Avg</th>
                    <th className="py-2">LTP</th>
                    <th className="py-2">P/L</th>
                    <th className="py-2">P/L %</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {(data.positions || []).map((p: any, idx: number) => (
                    <tr key={idx}>
                      <td className="py-2 text-white">{p.symbol}</td>
                      <td className="py-2 text-gray-300">{p.qty}</td>
                      <td className="py-2 text-gray-300">{p.avg_price}</td>
                      <td className="py-2 text-gray-300">{p.ltp}</td>
                      <td className={`py-2 ${p.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>₹{p.pnl?.toFixed?.(2) ?? p.pnl}</td>
                      <td className={`py-2 ${p.pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>{p.pnl_pct?.toFixed?.(2) ?? p.pnl_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Holdings */}
          <div>
            <p className="text-white font-medium mb-2">Holdings</p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 text-left">
                    <th className="py-2">Symbol</th>
                    <th className="py-2">Qty</th>
                    <th className="py-2">Avg</th>
                    <th className="py-2">LTP</th>
                    <th className="py-2">P/L</th>
                    <th className="py-2">P/L %</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {(data.holdings || []).map((h: any, idx: number) => (
                    <tr key={idx}>
                      <td className="py-2 text-white">{h.symbol}</td>
                      <td className="py-2 text-gray-300">{h.qty}</td>
                      <td className="py-2 text-gray-300">{h.avg_price}</td>
                      <td className="py-2 text-gray-300">{h.ltp}</td>
                      <td className={`py-2 ${h.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>₹{h.pnl?.toFixed?.(2) ?? h.pnl}</td>
                      <td className={`py-2 ${h.pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>{h.pnl_pct?.toFixed?.(2) ?? h.pnl_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Orders */}
          <div>
            <p className="text-white font-medium mb-2">Recent Orders</p>
            <ul className="divide-y divide-gray-700">
              {(data.orders || []).slice(0, 10).map((o: any, idx: number) => (
                <li key={idx} className="py-2 flex items-center justify-between">
                  <div>
                    <p className="text-white text-sm">{o.tradingSymbol || o.symbol}</p>
                    <p className="text-xs text-gray-500">{o.orderTime || o.timestamp}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-gray-300 text-sm">Qty: {o.quantity || o.qty}</p>
                    <p className={`text-xs ${o.orderStatus === 'completed' || o.status === 'completed' ? 'text-green-400' : 'text-gray-400'}`}>{o.orderStatus || o.status}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
