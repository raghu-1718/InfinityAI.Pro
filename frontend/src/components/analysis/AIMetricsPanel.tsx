export default function AIMetricsPanel() {
  return (
    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
      <h3 className="text-white font-semibold mb-2">AI Metrics</h3>
      <ul className="text-gray-300 text-sm space-y-1">
        <li>Model ensemble: active</li>
        <li>Feature pipeline: online</li>
        <li>Latency: <span className="text-green-400">OK</span></li>
      </ul>
    </div>
  )
}
