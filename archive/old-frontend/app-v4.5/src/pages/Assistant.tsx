import { useState } from 'react'

export default function Assistant() {
  const [q, setQ] = useState('')
  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Assistant</h1>
      <input value={q} onChange={e => setQ(e.target.value)} placeholder="Ask trading questions…" className="w-full max-w-lg p-2 rounded bg-gray-900 border border-gray-800" />
      <div className="text-gray-500 text-sm mt-2">Chat integration is wired via Engine D in production.</div>
    </div>
  )
}
