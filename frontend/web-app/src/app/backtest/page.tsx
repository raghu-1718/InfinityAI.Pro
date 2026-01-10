'use client';

import LivePriceCard from '@/components/LivePriceCard';
import PriceChart from '@/components/PriceChart';
import SignalsList from '@/components/SignalsList';

const SYMBOLS = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX', 'GOLD', 'CRUDEOIL'];

export default function BacktestDashboard() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
          InfinityAI.Pro Trading Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Real-time market data, backtesting results, and AI-powered trading signals
        </p>
      </div>

      {/* Live Prices Grid */}
      <section className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Live Market Prices
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {SYMBOLS.map((symbol) => (
            <LivePriceCard key={symbol} symbol={symbol} refreshInterval={30000} />
          ))}
        </div>
      </section>

      {/* Charts Section */}
      <section className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Price Charts (24-hour)
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PriceChart symbol="NIFTY" hours={24} />
          <PriceChart symbol="BANKNIFTY" hours={24} />
          <PriceChart symbol="GOLD" hours={24} />
          <PriceChart symbol="CRUDEOIL" hours={24} />
        </div>
      </section>

      {/* Trading Signals */}
      <section>
        <SignalsList refreshInterval={30000} maxSignals={15} />
      </section>
    </div>
  );
}
