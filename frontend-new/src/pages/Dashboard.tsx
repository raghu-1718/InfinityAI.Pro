
import { useEngineHealth } from '../hooks/useEngineHealth'
import { usePortfolio } from '../hooks/usePortfolio'
import LiveEngineGrid from '../components/dashboard/LiveEngineGrid'
import DashboardCard from '../components/dashboard/DashboardCard'
import TokenStatusCard from '../components/dashboard/TokenStatusCard'
import HoldingsAnalysisCard from '../components/dashboard/HoldingsAnalysisCard'
import { Wallet, TrendingUp, Cpu } from 'lucide-react'


export default function Dashboard() {
  const { data: engines } = useEngineHealth()
  const { data: portfolio, isLoading: loadingPortfolio } = usePortfolio()
  const healthyEngines = engines?.filter(e => e.healthy).length || 0
  const totalEngines = engines?.length || 4

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400 mt-1">Real-time trading intelligence platform</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500">Last Updated</p>
          <p className="text-sm text-green-400 font-mono">{new Date().toLocaleTimeString()}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <DashboardCard
          title="Portfolio Value"
          value={loadingPortfolio ? 'Loading...' : `₹${portfolio?.value?.toLocaleString?.() ?? '--'}`}
          trend={loadingPortfolio ? '' : (portfolio?.pnl && portfolio.pnl >= 0 ? `+${portfolio.pnl.toLocaleString?.()}` : `${portfolio?.pnl?.toLocaleString?.() ?? ''}`)}
          icon={<Wallet className="text-green-400" size={20} />}
        />
        <DashboardCard
          title="Today's P&L"
          value={loadingPortfolio ? 'Loading...' : `₹${portfolio?.pnl?.toLocaleString?.() ?? '--'}`}
          trend={loadingPortfolio ? '' : (portfolio?.pnl && portfolio.pnl >= 0 ? '+1.2%' : '-1.2%')}
          icon={<TrendingUp className="text-green-400" size={20} />}
        />
        <DashboardCard
          title="Active Engines"
          value={`${healthyEngines}/${totalEngines}`}
          trend={healthyEngines === totalEngines ? 'All Online' : 'Degraded'}
          icon={<Cpu className="text-green-400" size={20} />}
        />
      </div>

      {/* Token Status & Holdings Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TokenStatusCard />
        <HoldingsAnalysisCard />
      </div>

      <div>
        <h2 className="text-xl font-bold text-white mb-4">Engine Status</h2>
        <LiveEngineGrid />
      </div>
    </div>
  )
}

