
import DashboardCard from '../components/dashboard/DashboardCard';
import { Wallet, TrendingUp, Cpu } from 'lucide-react';
import EngineHealth from '../components/dashboard/EngineHealth';
import AISignals from '../components/dashboard/AISignals';
import TradeLog from '../components/dashboard/TradeLog';

export default function Dashboard() {

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
          value={`$12,345.67`}
          trend={`+1.2%`}
          icon={<Wallet className="text-green-400" size={20} />}
        />
        <DashboardCard
          title="Today's P&L"
          value={`$123.45`}
          trend={`+0.5%`}
          icon={<TrendingUp className="text-green-400" size={20} />}
        />
        <DashboardCard
          title="Active Engines"
          value={`4/4`}
          trend={`All Online`}
          icon={<Cpu className="text-green-400" size={20} />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <EngineHealth />
        <AISignals />
      </div>

      <div>
        <TradeLog />
      </div>
    </div>
  )
}
