import { useState } from 'react'
import { useAuthStore } from '../store/authStore'
import axios from 'axios'
import { MessageSquare, Send } from 'lucide-react'

const ENGINE_D_URL = import.meta.env.VITE_ENGINE_D_URL

interface Message {
  role: 'user' | 'ai'
  content: string
  timestamp: string
}

export default function Assistant() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const { getAuthHeader, ensureTokenValid } = useAuthStore()

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    }])

    setLoading(true)
    try {
      await ensureTokenValid()
      const res = await axios.post(
        `${ENGINE_D_URL}/api/chat`,
        {
          user_id: 'frontend-user',
          message: userMessage
        },
        { headers: getAuthHeader() }
      )

      setMessages(prev => [...prev, {
        role: 'ai',
        content: res.data.response || 'No response received',
        timestamp: new Date().toISOString()
      }])
    } catch (error: any) {
      setMessages(prev => [...prev, {
        role: 'ai',
        content: `Error: ${error.response?.data?.message || error.message}`,
        timestamp: new Date().toISOString()
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <MessageSquare className="text-green-400" />
          AI Assistant
        </h1>
        <p className="text-gray-400 mt-1">Powered by Engine D - Your intelligent trading companion</p>
      </div>

      <div className="flex-1 bg-gray-900 rounded-xl border border-gray-800 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center text-gray-500">
              <div className="text-center">
                <MessageSquare size={64} className="mx-auto mb-4 opacity-20" />
                <p>Start a conversation with your AI assistant</p>
                <p className="text-sm mt-2">Ask about system status, market data, or trading strategies</p>
              </div>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[70%] p-4 rounded-2xl ${
                    msg.role === 'user'
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-800 text-gray-100 border border-gray-700'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                  <p className="text-xs opacity-60 mt-2">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-800 border border-gray-700 p-4 rounded-2xl">
                <div className="flex gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce delay-100" />
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce delay-200" />
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-gray-800">
          <div className="flex gap-3">
            <input
              className="flex-1 bg-gray-800 text-white p-4 rounded-xl outline-none focus:ring-2 focus:ring-green-600 border border-gray-700"
              placeholder="Ask the AI assistant..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="bg-green-600 px-6 rounded-xl hover:bg-green-500 disabled:bg-gray-700 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <Send size={20} />
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
