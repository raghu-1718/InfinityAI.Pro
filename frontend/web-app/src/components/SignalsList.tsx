'use client';

import { useEffect, useState } from 'react';
import { TradingSignal, getLatestSignals } from '@/lib/backtestApi';

interface SignalsListProps {
  refreshInterval?: number;
  maxSignals?: number;
}

export default function SignalsList({ refreshInterval = 30000, maxSignals = 10 }: SignalsListProps) {
  const [signals, setSignals] = useState<TradingSignal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSignals = async () => {
    try {
      const response = await getLatestSignals();
      if (response.status === 'success') {
        setSignals(response.signals.slice(0, maxSignals));
        setError(null);
      } else {
        setError(response.error || 'Failed to load signals');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval, maxSignals]);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  const getSignalColor = (type: string) => {
    switch (type) {
      case 'BUY':
        return 'bg-green-100 dark:bg-green-900/30 border-green-500 text-green-700 dark:text-green-400';
      case 'SELL':
        return 'bg-red-100 dark:bg-red-900/30 border-red-500 text-red-700 dark:text-red-400';
      default:
        return 'bg-gray-100 dark:bg-gray-700 border-gray-500 text-gray-700 dark:text-gray-400';
    }
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-500';
    if (confidence >= 0.6) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white">
          Trading Signals
        </h3>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {signals.length} active
          </span>
        </div>
      </div>

      {/* Signals List */}
      {error ? (
        <div className="text-center py-8 text-red-500">{error}</div>
      ) : signals.length === 0 ? (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          No active signals at the moment
        </div>
      ) : (
        <div className="space-y-3">
          {signals.map((signal, index) => (
            <div
              key={index}
              className={`${getSignalColor(signal.signal_type)} border-2 rounded-lg p-4 transition-all hover:scale-102`}
            >
              <div className="flex justify-between items-start mb-2">
                {/* Symbol & Signal Type */}
                <div className="flex items-center gap-3">
                  <h4 className="text-lg font-bold">{signal.symbol}</h4>
                  <span className="px-3 py-1 rounded-full text-sm font-semibold bg-white dark:bg-gray-800">
                    {signal.signal_type}
                  </span>
                </div>

                {/* Timestamp */}
                <span className="text-xs opacity-75">
                  {new Date(signal.timestamp).toLocaleString('en-IN', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>

              {/* Strategy & Confidence */}
              <div className="flex items-center gap-4 mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm opacity-75">Strategy:</span>
                  <span className="text-sm font-semibold">{signal.strategy}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm opacity-75">Confidence:</span>
                  <div className="flex items-center gap-1">
                    <div className={`w-2 h-2 ${getConfidenceBadge(signal.confidence)} rounded-full`}></div>
                    <span className="text-sm font-semibold">
                      {(signal.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Price */}
              <div className="flex items-center gap-2">
                <span className="text-sm opacity-75">Entry Price:</span>
                <span className="text-lg font-bold">
                  ₹{signal.price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              </div>

              {/* Indicators */}
              {signal.indicators && Object.keys(signal.indicators).length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-300 dark:border-gray-600">
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    {Object.entries(signal.indicators).map(([key, value]) => (
                      <div key={key}>
                        <span className="opacity-75">{key}:</span>
                        <span className="ml-1 font-semibold">
                          {typeof value === 'number' ? value.toFixed(2) : value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Auto-refresh indicator */}
      <div className="mt-4 text-center text-xs text-gray-500 dark:text-gray-400">
        Auto-refreshing every {refreshInterval / 1000}s
      </div>
    </div>
  );
}
