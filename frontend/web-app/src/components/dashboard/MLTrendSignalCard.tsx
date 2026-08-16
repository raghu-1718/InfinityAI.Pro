import React from 'react';
import { TrendingUp, TrendingDown, Target, ShieldAlert, Cpu, Activity } from 'lucide-react';

export interface MLSignalPayload {
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  current_price: number;
  predicted_price: number;
  stop_loss: number;
  target: number;
  model_version: string;
  data_source: string;
  exchange_segment: string;
  analysis: {
    rsi: number;
    adx: number;
    trend: string;
    score: number;
    asset_class: string;
    key_factors: string[];
  };
  user_id: string;
  timestamp: string;
}

export const MLTrendSignalCard: React.FC<{ data: MLSignalPayload }> = ({ data }) => {
  const isBuy = data.signal === 'BUY';
  const signalColor = isBuy ? 'text-emerald-400' : data.signal === 'SELL' ? 'text-rose-400' : 'text-amber-400';
  const badgeBg = isBuy ? 'bg-emerald-500/10 border-emerald-500/30' : data.signal === 'SELL' ? 'bg-rose-500/10 border-rose-500/30' : 'bg-amber-500/10 border-amber-500/30';
  const normalizedConfidence = data.confidence > 1 ? data.confidence : data.confidence * 100;

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-5 shadow-2xl text-zinc-100 w-full">
      {/* Header */}
      <div className="flex justify-between items-start border-b border-zinc-800/80 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-xl font-bold tracking-wide">{data.symbol}</h3>
            <span className="text-xs px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 font-mono">
              {data.exchange_segment} • {data.analysis.asset_class}
            </span>
          </div>
          <p className="text-xs text-zinc-500 mt-1">
            Model: <span className="font-mono text-zinc-400">{data.model_version}</span> ({data.data_source.toUpperCase()})
          </p>
        </div>

        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${badgeBg}`}>
          {isBuy ? <TrendingUp className="w-5 h-5 text-emerald-400" /> : <TrendingDown className="w-5 h-5 text-rose-400" />}
          <span className={`text-base font-extrabold ${signalColor}`}>{data.signal}</span>
          <span className="text-xs text-zinc-400 font-mono">({Math.min(normalizedConfidence, 100).toFixed(1)}%)</span>
        </div>
      </div>

      {/* Price Target Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 my-4">
        <div className="bg-zinc-900/60 p-2.5 rounded-lg border border-zinc-800/60 text-center">
          <span className="text-[10px] text-zinc-500 font-semibold block uppercase">LTP</span>
          <span className="text-sm font-bold text-white font-mono">₹{data.current_price.toFixed(2)}</span>
        </div>
        <div className="bg-zinc-900/60 p-2.5 rounded-lg border border-zinc-800/60 text-center">
          <span className="text-[10px] text-indigo-400 font-semibold block uppercase">Predicted</span>
          <span className="text-sm font-bold text-indigo-300 font-mono">₹{data.predicted_price.toFixed(2)}</span>
        </div>
        <div className="bg-zinc-900/60 p-2.5 rounded-lg border border-zinc-800/60 text-center">
          <span className="text-[10px] text-emerald-400 font-semibold block uppercase flex items-center justify-center gap-0.5">
            <Target className="w-3 h-3" /> Target
          </span>
          <span className="text-sm font-bold text-emerald-400 font-mono">₹{data.target.toFixed(2)}</span>
        </div>
        <div className="bg-zinc-900/60 p-2.5 rounded-lg border border-zinc-800/60 text-center">
          <span className="text-[10px] text-rose-400 font-semibold block uppercase flex items-center justify-center gap-0.5">
            <ShieldAlert className="w-3 h-3" /> Stop Loss
          </span>
          <span className="text-sm font-bold text-rose-400 font-mono">₹{data.stop_loss.toFixed(2)}</span>
        </div>
      </div>

      {/* Technical Indicators */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-zinc-900/40 px-3 py-2 rounded-lg border border-zinc-800/40 text-xs">
        <div className="flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-zinc-400" />
          <span className="text-zinc-400">RSI:</span>
          <span className="font-mono font-semibold text-white">{data.analysis.rsi}</span>
        </div>
        <div>
          <span className="text-zinc-400">ADX: </span>
          <span className="font-mono font-semibold text-white">{data.analysis.adx}</span>
        </div>
        <div>
          <span className="text-zinc-400">Trend: </span>
          <span className="font-semibold text-emerald-400">{data.analysis.trend}</span>
        </div>
        <div>
          <span className="text-zinc-400">AI Score: </span>
          <span className="font-mono font-bold text-indigo-400">{data.analysis.score}/5</span>
        </div>
      </div>

      {/* Key Factors Chips */}
      <div className="mt-4">
        <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block mb-1.5">
          Signal Key Catalysts
        </span>
        <div className="flex flex-wrap gap-1.5">
          {data.analysis.key_factors.map((factor, idx) => (
            <span
              key={idx}
              className="text-xs bg-zinc-900 border border-zinc-700/60 text-zinc-300 px-2.5 py-1 rounded-md flex items-center gap-1"
            >
              <Cpu className="w-3 h-3 text-indigo-400" />
              {factor}
            </span>
          ))}
        </div>
      </div>

      {/* Footer / Timestamp */}
      <div className="mt-4 pt-3 border-t border-zinc-800/80 flex justify-between items-center text-[10px] text-zinc-500 font-mono">
        <span>UID: {data.user_id}</span>
        <span>
          {(() => {
            if (!data.timestamp) return 'Live IST';
            const raw = data.timestamp;
            // Append Z if no timezone offset is provided to ensure correct UTC parsing
            const iso = (raw.endsWith('Z') || raw.includes('+') || (raw.includes('-') && raw.length > 19)) ? raw : `${raw}Z`;
            try {
              const d = new Date(iso);
              if (isNaN(d.getTime())) return `${raw} IST`;
              return d.toLocaleString('en-IN', {
                timeZone: 'Asia/Kolkata',
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true
              }) + ' IST';
            } catch {
              return `${raw} IST`;
            }
          })()}
        </span>
      </div>
    </div>
  );
};
