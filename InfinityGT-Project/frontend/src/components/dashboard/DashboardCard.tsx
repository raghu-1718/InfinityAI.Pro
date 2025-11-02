import { TrendingUp, TrendingDown } from 'lucide-react'

interface DashboardCardProps {
  title: string
  value: string
  trend: string
  icon?: React.ReactNode
}

export default function DashboardCard({ title, value, trend, icon }: DashboardCardProps) {
  const isPositive = trend.startsWith('+')
  
  return (
    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 hover:border-green-600 transition-all duration-300">
      <div className="flex justify-between items-start mb-4">
        <p className="text-gray-400 text-sm font-medium">{title}</p>
        {icon || (isPositive ? (
          <TrendingUp className="text-green-400" size={20} />
        ) : (
          <TrendingDown className="text-red-400" size={20} />
        ))}
      </div>
      <p className="text-3xl font-bold text-white mb-2">{value}</p>
      <p className={`text-sm font-medium ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
        {trend}
      </p>
    </div>
  )
}
