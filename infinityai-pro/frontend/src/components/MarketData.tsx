import React, { useState, useEffect } from 'react';
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon, MinusIcon } from '@heroicons/react/24/outline';

interface MarketIndex {
  symbol: string;
  name: string;
  value: number;
  change: number;
  changePercent: number;
  volume?: number;
}

interface MarketDataProps {
  indices?: MarketIndex[];
}

const MarketData: React.FC<MarketDataProps> = ({ indices }) => {
  const [marketIndices, setMarketIndices] = useState<MarketIndex[]>(indices || [
    {
      symbol: 'NIFTY 50',
      name: 'Nifty 50',
      value: 22150.75,
      change: 184.25,
      changePercent: 0.84,
      volume: 245678900
    },
    {
      symbol: 'BANKNIFTY',
      name: 'Bank Nifty',
      value: 44800.50,
      change: -125.75,
      changePercent: -0.28,
      volume: 98765432
    },
    {
      symbol: 'SENSEX',
      name: 'BSE Sensex',
      value: 72500.25,
      change: 312.80,
      changePercent: 0.43,
      volume: 156789012
    }
  ]);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMarketIndices(prev =>
        prev.map(index => ({
          ...index,
          value: index.value + (Math.random() - 0.5) * 10,
          change: index.change + (Math.random() - 0.5) * 5,
          changePercent: index.changePercent + (Math.random() - 0.5) * 0.1
        }))
      );
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0
    }).format(value);
  };

  const formatVolume = (volume: number) => {
    if (volume >= 10000000) {
      return `${(volume / 10000000).toFixed(1)}Cr`;
    } else if (volume >= 100000) {
      return `${(volume / 100000).toFixed(1)}L`;
    }
    return volume.toString();
  };

  const getChangeIcon = (change: number) => {
    if (change > 0) return <ArrowTrendingUpIcon className="w-4 h-4 text-green-600" />;
    if (change < 0) return <ArrowTrendingDownIcon className="w-4 h-4 text-red-600" />;
    return <MinusIcon className="w-4 h-4 text-gray-600" />;
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">Market Overview</h2>
        <p className="text-sm text-gray-600 mt-1">Real-time market indices and key indicators</p>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {marketIndices.map((index, idx) => (
            <div key={idx} className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-900">{index.symbol}</h3>
                {getChangeIcon(index.change)}
              </div>

              <div className="space-y-1">
                <p className="text-lg font-bold text-gray-900">
                  {formatCurrency(index.value)}
                </p>

                <div className={`flex items-center text-sm font-medium ${getChangeColor(index.change)}`}>
                  <span className="mr-1">
                    {index.change >= 0 ? '+' : ''}{index.change.toFixed(2)}
                  </span>
                  <span>
                    ({index.changePercent >= 0 ? '+' : ''}{index.changePercent.toFixed(2)}%)
                  </span>
                </div>

                {index.volume && (
                  <p className="text-xs text-gray-500">
                    Vol: {formatVolume(index.volume)}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Market Status */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-gray-900">Market Status</h3>
              <p className="text-xs text-gray-600 mt-1">Indian markets are currently open</p>
            </div>

            <div className="text-right">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                <span className="text-sm font-medium text-green-600">Open</span>
              </div>
              <p className="text-xs text-gray-600 mt-1">
                Closes in 2h 15m
              </p>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-xs text-gray-600">Advances</p>
            <p className="text-lg font-bold text-green-600">1,247</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-600">Declines</p>
            <p className="text-lg font-bold text-red-600">987</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-600">Unchanged</p>
            <p className="text-lg font-bold text-gray-600">156</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-600">52W High</p>
            <p className="text-lg font-bold text-blue-600">23</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketData;