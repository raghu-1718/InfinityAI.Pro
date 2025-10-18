import { useAIAnalysis } from '../hooks/useAIAnalysis'

export default function Analysis() {
  const { data, isLoading, error } = useAIAnalysis()
  if (isLoading) return <div>Loading AI signals…</div>
  if (error) return <div className="text-red-400">Failed to load analysis.</div>
  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">AI Analysis</h1>
      <pre className="bg-gray-900 border border-gray-800 p-3 rounded text-xs overflow-auto">{JSON.stringify(data, null, 2)}</pre>
    </div>
  )
}
