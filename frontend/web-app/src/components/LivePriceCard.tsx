'use client';

import { useEffect, useState } from 'react';
import { LivePrice, getLivePrices } from '@/lib/backtestApi';

interface LivePriceCardProps {
  symbol: string;
  refreshInterval?: number; // milliseconds
}

export default function LivePriceCard({ symbol, refreshInterval = 30000 }: LivePriceCardProps) {
  const [price, setPrice] = useState<LivePrice | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPrice = async () => {
    try {
      const response = await getLivePrices();
      if (response.status === 'success' && response.prices[symbol]) {
        setPrice(response.prices[symbol]);
        setError(null);
      } else {
        setError('Symbol not found');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch price');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrice();
    const interval = setInterval(fetchPrice, refreshInterval);
    return () => clearInterval(interval);
  }, [symbol, refreshInterval]);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 animate-pulse">
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4"></div>
        <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
      </div>
    );
  }

  if (error || !price) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 border-2 border-red-500">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">{symbol}</h3>
        <p className="text-red-500">{ error || 'No data available'}</p>
      </div>
    );
  }

  const changePct = price.change_percent ?? price.changePercent ?? 0;
  const openPrice = price.open ?? price.price ?? 0;
  const isPositive = changePct >= 0;
  const priceColor = isPositive ? 'text-green-600' : 'text-red-600';
  const bgColor = isPositive ? 'bg-green-50 dark:bg-green-900/20' : 'bg-red-50 dark:bg-red-900/20';

  return (
    <div className={`${bgColor} rounded-lg shadow-lg p-6 transition-all hover:scale-105`}>
      {/* Symbol Header */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white">{symbol}</h3>
        <span className="text-xs text-gray-500">
          {new Date(price.timestamp).toLocaleTimeString()}
        </span>
      </div>

      {/* Current Price */}
      <div className="mb-3">
        <div className="text-3xl font-bold text-gray-900 dark:text-white">
          ₹{price.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        <div className={`text-sm font-semibold ${priceColor} flex items-center gap-1`}>
          <span>{isPositive ? '▲' : '▼'}</span>
          <span>{Math.abs(changePct).toFixed(2)}%</span>
        </div>
      </div>

      {/* OHLV Details */}
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <span className="text-gray-500 dark:text-gray-400">Open:</span>
          <span className="ml-2 font-medium text-gray-900 dark:text-white">
            ₹{openPrice.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">High:</span>
          <span className="ml-2 font-medium text-gray-900 dark:text-white">
            ₹{price.high.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">Low:</span>
          <span className="ml-2 font-medium text-gray-900 dark:text-white">
            ₹{price.low.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">Volume:</span>
          <span className="ml-2 font-medium text-gray-900 dark:text-white">
            {(price.volume / 1000).toFixed(0)}K
          </span>
        </div>
      </div>

      {/* Live Indicator */}
      <div className="mt-4 flex items-center gap-2">
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
        <span className="text-xs text-gray-600 dark:text-gray-400">Live</span>
      </div>
    </div>
  );
}
