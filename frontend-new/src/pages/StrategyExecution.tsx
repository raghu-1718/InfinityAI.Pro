import ExecutionPanel from '../components/strategy/ExecutionPanel'

export default function StrategyExecution() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Strategy Execution</h1>
      <p className="text-gray-400">Execute and monitor trading strategies in real-time</p>
      <ExecutionPanel />
    </div>
  )
}
