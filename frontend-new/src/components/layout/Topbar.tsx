import { Bell, Search } from 'lucide-react'
import { useEngineHealth } from '../../hooks/useEngineHealth'

export default function Topbar() {
  const { data: engines } = useEngineHealth()
  const healthyEngines = engines?.filter(e => e.healthy).length || 0
  const totalEngines = engines?.length || 4

  return (
    <header className="bg-gray-900 border-b border-gray-800 h-16 flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
          <input
            type="text"
            placeholder="Search..."
            className="bg-gray-800 text-gray-300 pl-10 pr-4 py-2 rounded-lg w-64 focus:outline-none focus:ring-2 focus:ring-green-600"
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-4 py-2 bg-gray-800 rounded-lg">
          <div className={`w-2 h-2 rounded-full ${healthyEngines === totalEngines ? 'bg-green-500' : 'bg-yellow-500'} animate-pulse`} />
          <span className="text-sm text-gray-300">
            {healthyEngines}/{totalEngines} Engines Online
          </span>
        </div>

        <button className="relative p-2 hover:bg-gray-800 rounded-lg transition-colors">
          <Bell size={20} className="text-gray-400" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </button>
      </div>
    </header>
  )
}
