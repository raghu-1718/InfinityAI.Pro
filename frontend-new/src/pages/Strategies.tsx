import { useStrategies } from '../hooks/useStrategies'

export default function Strategies() {
  const { data: strategies, isLoading, error } = useStrategies()

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Trading Strategies</h1>
      <p className="text-gray-400">Manage and monitor your trading strategies</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {isLoading && <p className="text-gray-400">Loading strategies...</p>}
        {error && <p className="text-red-400">Failed to load strategies.</p>}
        {strategies?.map((strategy, i) => (
          <div key={i} className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h3 className="text-xl font-bold text-white mb-2">{strategy.name}</h3>
            <p className="text-gray-400 mb-4">{strategy.description}</p>
            <span className={`px-4 py-2 rounded-lg ${
              strategy.status === 'active' ? 'bg-green-600' : 'bg-gray-600'
            }`}>
              {strategy.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
