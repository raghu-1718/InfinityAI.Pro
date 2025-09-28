import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/outline';

interface Position {
  symbol: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercentage: number;
}

const PortfolioOverview: React.FC = () => {
  const [portfolioData, setPortfolioData] = useState({
    totalValue: 125000,
    totalPnl: 2450,
    totalPnlPercentage: 2.0,
    dayChange: 1840,
    dayChangePercentage: 1.5
  });

  const [positions] = useState<Position[]>([
    {
      symbol: 'NIFTY',
      quantity: 50,
      avgPrice: 21800,
      currentPrice: 22150,
      pnl: 1750,
      pnlPercentage: 1.6
    },
    {
      symbol: 'BANKNIFTY',
      quantity: 25,
      avgPrice: 44500,
      currentPrice: 44800,
      pnl: 750,
      pnlPercentage: 0.7
    },
    {
      symbol: 'RELIANCE',
      quantity: 10,
      avgPrice: 2850,
      currentPrice: 2820,
      pnl: -300,
      pnlPercentage: -1.1
    }
  ]);

  const [chartData] = useState([
    { time: '09:00', value: 120000 },
    { time: '10:00', value: 121500 },
    { time: '11:00', value: 122800 },
    { time: '12:00', value: 123200 },
    { time: '13:00', value: 124500 },
    { time: '14:00', value: 123800 },
    { time: '15:00', value: 125000 }
  ]);

  const [allocationData] = useState([
    { name: 'NIFTY', value: 45, color: '#3B82F6' },
    { name: 'BANKNIFTY', value: 35, color: '#10B981' },
    { name: 'Stocks', value: 20, color: '#F59E0B' }
  ]);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setPortfolioData(prev => ({
        ...prev,
        totalValue: prev.totalValue + (Math.random() - 0.5) * 100,
        totalPnl: prev.totalPnl + (Math.random() - 0.5) * 50
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0
    }).format(value);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">Portfolio Overview</h2>
        <p className="text-sm text-gray-600 mt-1">Real-time portfolio performance and positions</p>
      </div>

      <div className="p-6">
        {/* Portfolio Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="text-center">
            <p className="text-sm text-gray-600">Total Value</p>
            <p className="text-2xl font-bold text-gray-900">{formatCurrency(portfolioData.totalValue)}</p>
            <div className="flex items-center justify-center mt-1">
              <ArrowTrendingUpIcon className="w-4 h-4 text-green-600 mr-1" />
              <span className="text-sm text-green-600">+{portfolioData.totalPnlPercentage.toFixed(1)}%</span>
            </div>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600">Today's P&L</p>
            <p className={`text-2xl font-bold ${portfolioData.totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {portfolioData.totalPnl >= 0 ? '+' : ''}{formatCurrency(portfolioData.totalPnl)}
            </p>
            <div className="flex items-center justify-center mt-1">
              <ArrowTrendingUpIcon className="w-4 h-4 text-green-600 mr-1" />
              <span className="text-sm text-green-600">+{portfolioData.dayChangePercentage.toFixed(1)}%</span>
            </div>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600">Active Positions</p>
            <p className="text-2xl font-bold text-gray-900">{positions.length}</p>
            <p className="text-sm text-gray-500 mt-1">Across 3 symbols</p>
          </div>
        </div>

        {/* Portfolio Chart */}
        <div className="mb-8">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Portfolio Value (Today)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="time"
                  stroke="#6B7280"
                  fontSize={12}
                  tickLine={false}
                />
                <YAxis
                  stroke="#6B7280"
                  fontSize={12}
                  tickLine={false}
                  tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}K`}
                />
                <Tooltip
                  formatter={(value: any) => [formatCurrency(value), 'Portfolio Value']}
                  labelStyle={{ color: '#374151' }}
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px'
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: '#3B82F6', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Asset Allocation */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Asset Allocation</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={allocationData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {allocationData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: any) => [`${value}%`, 'Allocation']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Legend</h3>
            <div className="space-y-3">
              {allocationData.map((item, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div
                      className="w-4 h-4 rounded mr-3"
                      style={{ backgroundColor: item.color }}
                    ></div>
                    <span className="text-sm font-medium text-gray-900">{item.name}</span>
                  </div>
                  <span className="text-sm text-gray-600">{item.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Positions Table */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Current Positions</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Symbol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Current Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    P&L
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {positions.map((position, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{position.symbol}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{position.quantity}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{formatCurrency(position.avgPrice)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{formatCurrency(position.currentPrice)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm font-medium ${position.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {position.pnl >= 0 ? '+' : ''}{formatCurrency(position.pnl)}
                        <span className="ml-1 text-xs">
                          ({position.pnlPercentage >= 0 ? '+' : ''}{position.pnlPercentage.toFixed(1)}%)
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioOverview;
