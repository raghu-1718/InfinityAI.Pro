import { useState } from 'react'
import { useDhanStatus, useDhanCallbackUrls, updateDhanAccessToken, updateDhanCredentials, initiateDhanOAuth } from '../hooks/useDhanIntegration'

export default function Settings() {
  const { data: dhanStatus } = useDhanStatus()
  const { data: callbackUrls } = useDhanCallbackUrls()
  const [accessToken, setAccessToken] = useState('')
  const [clientId, setClientId] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [apiSecret, setApiSecret] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  const saveAccessToken = async () => {
    setBusy(true)
    setMessage('')
    try {
      const res = await updateDhanAccessToken(accessToken, true)
      if ('error' in res) throw new Error(res.error)
      setMessage(`Access token updated${res.persisted ? ' and persisted to vault' : ''}`)
      setAccessToken('')
    } catch (e: any) {
      setMessage(`Failed to update token: ${e.message}`)
    } finally {
      setBusy(false)
    }
  }

  const saveCredentials = async () => {
    setBusy(true)
    setMessage('')
    try {
      const res = await updateDhanCredentials({ client_id: clientId || undefined, api_key: apiKey || undefined, api_secret: apiSecret || undefined })
      if ('error' in res) throw new Error(res.error)
      setMessage('Credentials updated')
      setClientId(''); setApiKey(''); setApiSecret('')
    } catch (e: any) {
      setMessage(`Failed to update credentials: ${e.message}`)
    } finally {
      setBusy(false)
    }
  }

  const startOAuth = async () => {
    try {
      const res = await initiateDhanOAuth()
      if (res.status === 'success' && res.auth_url) {
        window.location.href = res.auth_url
      }
    } catch (_) {
      // ignore
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Settings</h1>
      <p className="text-gray-400">Configure your trading platform preferences</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
          <h3 className="text-xl font-bold text-white mb-4">Dhan Integration</h3>
          <div className="text-gray-300 space-y-2">
            <div>Status: <span className="font-medium">{dhanStatus?.integration_status || 'loading...'}</span></div>
            <div>Connected: <span className="font-medium">{dhanStatus?.connected ? 'Yes' : 'No'}</span></div>
            <div>Client ID: <span className="font-mono">{dhanStatus?.client_id || '—'}</span></div>
            <div>Redirect URL: <span className="font-mono break-all">{callbackUrls?.redirect_url}</span></div>
            <div>Postback URL: <span className="font-mono break-all">{callbackUrls?.postback_url}</span></div>
          </div>
          <button onClick={startOAuth} className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-md text-white">Initiate Dhan OAuth</button>
        </div>

        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
          <h3 className="text-xl font-bold text-white mb-4">Update Access Token</h3>
          <div className="space-y-3">
            <input
              className="w-full bg-gray-900 text-white border border-gray-700 rounded-md px-3 py-2"
              type="password"
              placeholder="Paste Dhan access token"
              value={accessToken}
              onChange={(e) => setAccessToken(e.target.value)}
            />
            <button disabled={busy || accessToken.length < 10} onClick={saveAccessToken} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-md text-white">Save Token</button>
            {message && <div className="text-sm text-gray-300">{message}</div>}
          </div>
        </div>

        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
          <h3 className="text-xl font-bold text-white mb-4">Client Credentials</h3>
          <div className="space-y-3">
            <input className="w-full bg-gray-900 text-white border border-gray-700 rounded-md px-3 py-2" placeholder="Client ID" value={clientId} onChange={(e) => setClientId(e.target.value)} />
            <input className="w-full bg-gray-900 text-white border border-gray-700 rounded-md px-3 py-2" type="password" placeholder="API Key" value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
            <input className="w-full bg-gray-900 text-white border border-gray-700 rounded-md px-3 py-2" type="password" placeholder="API Secret" value={apiSecret} onChange={(e) => setApiSecret(e.target.value)} />
            <button disabled={busy || (!clientId && !apiKey && !apiSecret)} onClick={saveCredentials} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-md text-white">Save Credentials</button>
          </div>
        </div>

        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
          <h3 className="text-xl font-bold text-white mb-4">Notifications</h3>
          <p className="text-gray-400">Manage alert preferences</p>
        </div>

      </div>
    </div>
  )
}
