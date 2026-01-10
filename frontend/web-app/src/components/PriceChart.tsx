'use client';

import { useEffect, useState } from 'react';
import { PriceTick, getPriceHistory } from '@/lib/backtestApi';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface PriceChartProps {
  symbol: string;
  hours?: number;
  refreshInterval?: number;
}

export default function PriceChart({ symbol, hours = 24, refreshInterval = 60000 }: PriceChartProps) {
  const [data, setData] = useState<PriceTick[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const response = await getPriceHistory(symbol, hours);
      if (response.status === 'success') {
        setData(response.data);
        setError(null);
      } else {
        setError(response.error || 'Failed to load data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [symbol, hours, refreshInterval]);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
        <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
      </div>
    );
  }

  if (error || data.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4">{symbol} - {hours}h Chart</h3>
        <div className="h-64 flex items-center justify-center text-red-500">
          {error || 'No data available'}
        </div>
      </div>
    );
  }

  // Format data for chart
  const chartData = data.map((tick) => ({
    time: new Date(tick.timestamp).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
    }),
    price: tick.price,
    high: tick.high,
    low: tick.low,
  }));

  // Calculate price range for Y-axis domain
  const prices = data.map((t) => t.price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const padding = (maxPrice - minPrice) * 0.1;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {symbol} - {hours}h Price Chart
        </h3>
        <span className="text-sm text-gray-500">
          {data.length} data points
        </span>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
          <XAxis
            dataKey="time"
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[minPrice - padding, maxPrice + padding]}
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
            tickFormatter={(value) => `₹${value.toFixed(0)}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: 'none',
              borderRadius: '8px',
              color: '#F9FAFB',
            }}
            formatter={(value: number) => [
              `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
              'Price',
            ]}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="price"
            stroke="#10B981"
            strokeWidth={2}
            dot={false}
            name="Price"
          />
          <Line
            type="monotone"
            dataKey="high"
            stroke="#3B82F6"
            strokeWidth={1}
            strokeDasharray="5 5"
            dot={false}
            name="High"
          />
          <Line
            type="monotone"
            dataKey="low"
            stroke="#EF4444"
            strokeWidth={1}
            strokeDasharray="5 5"
            dot={false}
            name="Low"
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Stats */}
      <div className="mt-4 grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-xs text-gray-500 dark:text-gray-400">Current</div>
          <div className="text-lg font-semibold text-gray-900 dark:text-white">
            ₹{data[data.length - 1]?.price.toFixed(2)}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 dark:text-gray-400">High ({hours}h)</div>
          <div className="text-lg font-semibold text-blue-600">
            ₹{maxPrice.toFixed(2)}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 dark:text-gray-400">Low ({hours}h)</div>
          <div className="text-lg font-semibold text-red-600">
            ₹{minPrice.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
}
