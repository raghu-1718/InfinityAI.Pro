import { NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Cpu, 
  TrendingUp, 
  BarChart3, 
  MessageSquare, 
  Settings as SettingsIcon 
} from 'lucide-react'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/engines', label: 'Engines', icon: Cpu },
  { path: '/strategies', label: 'Strategies', icon: TrendingUp },
  { path: '/analysis', label: 'Analysis', icon: BarChart3 },
  { path: '/assistant', label: 'AI Assistant', icon: MessageSquare },
  { path: '/settings', label: 'Settings', icon: SettingsIcon },
]

export default function Sidebar() {
  return (
    <aside className="bg-gray-900 text-gray-200 w-64 h-full flex flex-col border-r border-gray-800">
      <div className="p-6 border-b border-gray-800">
        <h1 className="text-2xl font-bold text-green-400 flex items-center gap-2">
          <span className="text-3xl">∞</span>
          InfinityAI.Pro
        </h1>
        <p className="text-xs text-gray-500 mt-1">Advanced Trading Intelligence</p>
      </div>
      
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 py-3 px-4 rounded-lg transition-all duration-200 ${
                isActive
                  ? 'bg-green-600 text-white shadow-lg shadow-green-600/50'
                  : 'hover:bg-gray-800 text-gray-300 hover:text-white'
              }`
            }
          >
            <item.icon size={20} />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-800">
        <div className="flex items-center gap-3 px-4 py-3 bg-gray-800 rounded-lg">
          <div className="w-10 h-10 rounded-full bg-green-600 flex items-center justify-center text-white font-bold">
            R
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium">Raghu</p>
            <p className="text-xs text-gray-500">Premium Account</p>
          </div>
        </div>
      </div>
    </aside>
  )
}
