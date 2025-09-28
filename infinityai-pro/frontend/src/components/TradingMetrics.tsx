import React, { useState, useEffect } from 'react';
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon, CurrencyDollarIcon, ChartBarIcon } from '@heroicons/react/24/outline';

interface MetricCardProps {
  title: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: React.ComponentType<{ className?: string }>;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, changeType, icon: Icon }) => {
  const changeColor = {
    positive: 'text-green-600',
    negative: 'text-red-600',
    neutral: 'text-gray-600'
  };

  const changeBg = {
    positive: 'bg-green-50',
    negative: 'bg-red-50',
    neutral: 'bg-gray-50'
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={`p-3 rounded-full ${changeBg[changeType]}`}>
          <Icon className={`w-6 h-6 ${changeColor[changeType]}`} />
        </div>
      </div>
      <div className="mt-4 flex items-center">
        {changeType === 'positive' && <ArrowTrendingUpIcon className="w-4 h-4 text-green-600 mr-1" />}
        {changeType === 'negative' && <ArrowTrendingDownIcon className="w-4 h-4 text-red-600 mr-1" />}
        <span className={`text-sm font-medium ${changeColor[changeType]}`}>
          {change}
        </span>
        <span className="text-sm text-gray-500 ml-1">from last month</span>
      </div>
    </div>
  );
};

const TradingMetrics: React.FC = () => {
  const [metrics, setMetrics] = useState({
    portfolioValue: '₹1,25,000',
    todaysPnL: '+₹2,450',
    winRate: '68%',
    activeTrades: '3'
  });

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        ...prev,
        todaysPnL: `+₹${(2450 + Math.random() * 500).toFixed(0)}`
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
      <MetricCard
        title="Portfolio Value"
        value={metrics.portfolioValue}
        change="+12.5%"
        changeType="positive"
        icon={CurrencyDollarIcon}
      />
      <MetricCard
        title="Today's P&L"
        value={metrics.todaysPnL}
        change="+8.2%"
        changeType="positive"
        icon={ArrowTrendingUpIcon}
      />
      <MetricCard
        title="Win Rate"
        value={metrics.winRate}
        change="+5.1%"
        changeType="positive"
        icon={ChartBarIcon}
      />
      <MetricCard
        title="Active Trades"
        value={metrics.activeTrades}
        change="0"
        changeType="neutral"
        icon={ChartBarIcon}
      />
    </div>
  );
};

export default TradingMetrics;
