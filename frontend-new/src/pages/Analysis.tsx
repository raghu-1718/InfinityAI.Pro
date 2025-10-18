import SentimentHeatmap from '../components/analysis/SentimentHeatmap'
import CorrelationRadar from '../components/analysis/CorrelationRadar'
import AIMetricsPanel from '../components/analysis/AIMetricsPanel'
import ExchangesPanel from '../components/analysis/ExchangesPanel'
import DhanOverviewPanel from '../components/analysis/DhanOverviewPanel'
import StatementPanel from '../components/analysis/StatementPanel'
import { useAIAnalysis } from '../hooks/useAIAnalysis'

export default function Analysis() {
  const { data, isLoading, error } = useAIAnalysis()

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">AI Market & Dhan Analytics</h1>
      <p className="text-gray-400">Advanced AI insights plus your Dhan account overview, statements, and exchanges.</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <SentimentHeatmap />
        <CorrelationRadar />
      </div>

      <AIMetricsPanel />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DhanOverviewPanel />
        <ExchangesPanel />
      </div>

      <StatementPanel />

      <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
        <h2 className="text-white font-semibold mb-4">Top AI Signals</h2>
        {isLoading && <p className="text-gray-400">Loading AI signals...</p>}
        {error && <p className="text-red-400">Failed to load signals.</p>}
        {!isLoading && !error && (
          <ul className="divide-y divide-gray-700">
            {(data?.signals || []).slice(0, 10).map((s: any, idx: number) => (
              <li key={idx} className="py-3 flex items-center justify-between">
                <div>
                  <p className="text-white font-medium">{s.symbol}</p>
                  <p className="text-gray-500 text-sm">{new Date(s.timestamp).toLocaleString()}</p>
                </div>
                <div className="text-right">
                  <p className={`font-semibold ${s.direction === 'BUY' ? 'text-green-400' : s.direction === 'SELL' ? 'text-red-400' : 'text-gray-300'}`}>{s.direction}</p>
                  <p className="text-gray-400 text-sm">Score: {s.score?.toFixed?.(2) ?? s.score}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
