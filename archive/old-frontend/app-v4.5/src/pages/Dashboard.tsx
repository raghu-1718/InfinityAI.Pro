import { useEffect, useState } from 'react'
import { useWebSocketFeed } from '../hooks/useWebSocketFeed'

export default function Dashboard() {
  const [events, setEvents] = useState<any[]>([])
  useWebSocketFeed((d) => setEvents((e) => [d, ...e].slice(0, 50)))
  useEffect(() => {}, [])
  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Live Dashboard</h1>
      <div className="grid gap-3">
        {events.map((e, i) => (
          <pre key={i} className="bg-gray-900 border border-gray-800 p-3 rounded text-xs overflow-auto">{JSON.stringify(e, null, 2)}</pre>
        ))}
        {events.length === 0 && <div className="text-gray-400">Waiting for live updates…</div>}
      </div>
    </div>
  )
}
