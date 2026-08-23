import React from 'react';
import { Shield, TrendingUp, AlertTriangle } from 'lucide-react';

export default function RiskGauge({ score = 0, priority = 'LOW', reasons = [] }) {
  const normalizedScore = Math.max(0, Math.min(100, score));

  const getColor = (s) => {
    if (s >= 75) return { stroke: '#f43f5e', text: 'text-rose-400', glow: 'shadow-rose-500/20', bg: 'bg-rose-500/10' };
    if (s >= 50) return { stroke: '#f59e0b', text: 'text-amber-400', glow: 'shadow-amber-500/20', bg: 'bg-amber-500/10' };
    if (s >= 25) return { stroke: '#38bdf8', text: 'text-sky-400', glow: 'shadow-sky-500/20', bg: 'bg-sky-500/10' };
    return { stroke: '#22c55e', text: 'text-emerald-400', glow: 'shadow-emerald-500/20', bg: 'bg-emerald-500/10' };
  };

  const { stroke, text, bg } = getColor(normalizedScore);
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <div className="relative flex items-center justify-center">
        <svg className="w-24 h-24 transform -rotate-90">
          <circle
            cx="48"
            cy="48"
            r={radius}
            stroke="currentColor"
            strokeWidth="7"
            className="text-slate-800"
            fill="transparent"
          />
          <circle
            cx="48"
            cy="48"
            r={radius}
            stroke={stroke}
            strokeWidth="7"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        <div className="absolute flex flex-col items-center justify-center">
          <span className={`text-2xl font-black tracking-tighter font-mono ${text}`}>
            {normalizedScore}
          </span>
          <span className="text-[10px] uppercase font-semibold text-slate-400 -mt-1">
            /100
          </span>
        </div>
      </div>

      <div className="mt-2 text-center">
        <span className={`text-xs font-bold uppercase tracking-wider ${text}`}>
          {priority} RISK
        </span>
      </div>

      {reasons && reasons.length > 0 && (
        <div className="mt-3 w-full space-y-1">
          {reasons.slice(0, 3).map((r, idx) => (
            <div key={idx} className="text-[11px] text-slate-300 bg-slate-800/60 rounded px-2 py-1 flex items-start gap-1.5 border border-slate-700/50">
              <span className="text-civic-400 font-bold">•</span>
              <span className="leading-tight">{r}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
