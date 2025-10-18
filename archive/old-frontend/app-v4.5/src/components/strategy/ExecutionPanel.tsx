import axios from 'axios'
import { API } from '../../utils/constants'
import { useState } from 'react'
import { useAuthStore } from '../../store/authStore'

export default function ExecutionPanel() {
  const [busy, setBusy] = useState(false)
  const getAuthHeader = useAuthStore(s => s.getAuthHeader)
  async function start() {
    setBusy(true)
    try { await axios.post(API.tradeStart, {}, { headers: { ...getAuthHeader() } }) } finally { setBusy(false) }
  }
  async function stop() {
    setBusy(true)
    try { await axios.post(API.tradeStop, {}, { headers: { ...getAuthHeader() } }) } finally { setBusy(false) }
  }
  return (
    <div className="flex gap-3">
      <button disabled={busy} onClick={start} className="px-3 py-2 rounded bg-emerald-600 disabled:opacity-50">Start</button>
      <button disabled={busy} onClick={stop} className="px-3 py-2 rounded bg-rose-600 disabled:opacity-50">Stop</button>
    </div>
  )
}
