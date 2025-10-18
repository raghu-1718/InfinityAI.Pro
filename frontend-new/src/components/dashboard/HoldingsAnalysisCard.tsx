import { TrendingUp, TrendingDown, Package, Activity, Lightbulb } from 'lucide-react'
import { useHoldingsAnalysis } from '../../hooks/useHoldingsAnalysis'

export default function HoldingsAnalysisCard() {
  const { data, isLoading } = useHoldingsAnalysis()

  if (isLoading) {
    return (
      <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
        <div className="flex items-center gap-2 mb-4">
          <Package className="text-blue-400" size={20} />
          <h3 className="text-lg font-semibold text-white">Portfolio Analysis</h3>
        </div>
        <div className="animate-pulse space-y-2">
          <div className="h-4 bg-gray-700 rounded w-3/4"></div>
          <div className="h-4 bg-gray-700 rounded w-1/2"></div>
          <div className="h-4 bg-gray-700 rounded w-2/3"></div>
        </div>
      </div>
    )
  }

  const summary = data?.summary
  const holdings = data?.holdings || []
  const positions = data?.positions || []
  const insights = data?.insights || []
  const topGainers = data?.top_gainers || []
  const topLosers = data?.top_losers || []
  
  const totalHoldings = holdings.length + positions.length
  const isProfitable = (summary?.overall_pnl || 0) >= 0

  return (
    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 hover:border-green-600 transition-all duration-300">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Package className="text-green-400" size={20} />
          <h3 className="text-lg font-semibold text-white">Portfolio & Positions</h3>
        </div>
        {isProfitable ? (
          <TrendingUp className="text-green-400" size={18} />
        ) : (
          <TrendingDown className="text-red-400" size={18} />
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-900/50 p-3 rounded-lg">
          <p className="text-gray-400 text-xs mb-1">Total Invested</p>
          <p className="text-white font-semibold text-lg">
            ₹{summary?.total_invested?.toLocaleString() || '0'}
          </p>
        </div>
        <div className="bg-gray-900/50 p-3 rounded-lg">
          <p className="text-gray-400 text-xs mb-1">Current Value</p>
          <p className="text-white font-semibold text-lg">
            ₹{summary?.total_current?.toLocaleString() || '0'}
          </p>
        </div>
        <div className="bg-gray-900/50 p-3 rounded-lg">
          <p className="text-gray-400 text-xs mb-1">Overall P&L</p>
          <p className={`font-semibold text-lg ${isProfitable ? 'text-green-400' : 'text-red-400'}`}>
            ₹{summary?.overall_pnl?.toLocaleString() || '0'}
          </p>
        </div>
        <div className="bg-gray-900/50 p-3 rounded-lg">
          <p className="text-gray-400 text-xs mb-1">P&L %</p>
          <p className={`font-semibold text-lg ${isProfitable ? 'text-green-400' : 'text-red-400'}`}>
            {isProfitable ? '+' : ''}{summary?.overall_pct?.toFixed(2) || '0.00'}%
          </p>
        </div>
      </div>

      {/* Active Holdings & Positions */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
            <Activity className="text-blue-400" size={14} />
            Active Positions ({totalHoldings})
          </h4>
        </div>
        
        {totalHoldings === 0 ? (
          <div className="bg-gray-900/30 p-4 rounded-lg text-center">
            <p className="text-gray-500 text-sm">No active positions</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {/* Positions (Active Trades) */}
            {positions.map((pos, idx) => (
              <div 
                key={`pos-${idx}`}
                className="bg-blue-900/20 border border-blue-700/30 p-3 rounded-lg hover:border-blue-500 transition-colors"
              >
                <div className="flex justify-between items-start mb-1">
                  <div>
                    <p className="text-white font-semibold text-sm">{pos.symbol}</p>
                    <p className="text-gray-400 text-xs">
                      {pos.side || 'INTRADAY'} • Qty: {pos.qty}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className={`font-semibold text-sm ${pos.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {pos.pnl >= 0 ? '+' : ''}₹{pos.pnl.toLocaleString()}
                    </p>
                    <p className={`text-xs ${pos.pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      ({pos.pnl_pct >= 0 ? '+' : ''}{pos.pnl_pct.toFixed(2)}%)
                    </p>
                  </div>
                </div>
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Avg: ₹{pos.avg_price.toFixed(2)}</span>
                  <span>LTP: ₹{pos.ltp.toFixed(2)}</span>
                </div>
              </div>
            ))}
            
            {/* Holdings (Long-term) */}
            {holdings.map((holding, idx) => (
              <div 
                key={`hold-${idx}`}
                className="bg-gray-900/30 p-3 rounded-lg hover:bg-gray-900/50 transition-colors"
              >
                <div className="flex justify-between items-start mb-1">
                  <div>
                    <p className="text-white font-semibold text-sm">{holding.symbol}</p>
                    <p className="text-gray-400 text-xs">Holdings • Qty: {holding.qty}</p>
                  </div>
                  <div className="text-right">
                    <p className={`font-semibold text-sm ${holding.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {holding.pnl >= 0 ? '+' : ''}₹{holding.pnl.toLocaleString()}
                    </p>
                    <p className={`text-xs ${holding.pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      ({holding.pnl_pct >= 0 ? '+' : ''}{holding.pnl_pct.toFixed(2)}%)
                    </p>
                  </div>
                </div>
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Avg: ₹{holding.avg_price.toFixed(2)}</span>
                  <span>LTP: ₹{holding.ltp.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Top Movers */}
      {(topGainers.length > 0 || topLosers.length > 0) && (
        <div className="grid grid-cols-2 gap-3 mb-4">
          {topGainers.length > 0 && (
            <div className="bg-green-900/10 border border-green-700/30 p-3 rounded-lg">
              <p className="text-green-400 text-xs font-semibold mb-2">Top Gainer</p>
              <p className="text-white text-sm font-semibold">{topGainers[0].symbol}</p>
              <p className="text-green-400 text-xs">+{topGainers[0].pnl_pct.toFixed(2)}%</p>
            </div>
          )}
          {topLosers.length > 0 && (
            <div className="bg-red-900/10 border border-red-700/30 p-3 rounded-lg">
              <p className="text-red-400 text-xs font-semibold mb-2">Top Loser</p>
              <p className="text-white text-sm font-semibold">{topLosers[0].symbol}</p>
              <p className="text-red-400 text-xs">{topLosers[0].pnl_pct.toFixed(2)}%</p>
            </div>
          )}
        </div>
      )}

      {/* AI Insights */}
      {insights.length > 0 && (
        <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 border border-purple-700/30 p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb className="text-yellow-400" size={16} />
            <p className="text-yellow-400 text-xs font-semibold">AI Insights</p>
          </div>
          <div className="space-y-1">
            {insights.map((insight, idx) => (
              <p key={idx} className="text-gray-300 text-xs leading-relaxed">
                • {insight}
              </p>
            ))}
          </div>
        </div>
      )}

      {/* Available Funds */}
      {data?.funds && (
        <div className="mt-4 pt-4 border-t border-gray-700">
          <div className="flex justify-between items-center">
            <span className="text-gray-400 text-xs">Available Balance</span>
            <span className="text-green-400 font-semibold text-sm">
              ₹{data.funds.availabelBalance?.toLocaleString() || '0'}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
