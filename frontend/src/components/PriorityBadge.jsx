import React from 'react';
import { AlertTriangle, AlertCircle, Info, ShieldAlert, CheckCircle2 } from 'lucide-react';

export default function PriorityBadge({ priority = 'LOW', size = 'md' }) {
  const p = (priority || 'LOW').toUpperCase();

  const configs = {
    CRITICAL: {
      bg: 'bg-rose-500/15 border-rose-500/30 text-rose-400',
      dot: 'bg-rose-500 animate-pulse',
      icon: ShieldAlert,
      label: 'CRITICAL',
    },
    HIGH: {
      bg: 'bg-amber-500/15 border-amber-500/30 text-amber-400',
      dot: 'bg-amber-500',
      icon: AlertTriangle,
      label: 'HIGH',
    },
    MEDIUM: {
      bg: 'bg-blue-500/15 border-blue-500/30 text-blue-400',
      dot: 'bg-blue-500',
      icon: AlertCircle,
      label: 'MEDIUM',
    },
    LOW: {
      bg: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400',
      dot: 'bg-emerald-500',
      icon: CheckCircle2,
      label: 'LOW',
    },
    EXTERNAL: {
      bg: 'bg-purple-500/15 border-purple-500/30 text-purple-400',
      dot: 'bg-purple-500',
      icon: Info,
      label: 'EXTERNAL ROUTED',
    },
  };

  const current = configs[p] || configs.LOW;
  const Icon = current.icon;

  const sizeClasses = size === 'sm' 
    ? 'px-2 py-0.5 text-xs font-semibold' 
    : size === 'lg' 
    ? 'px-3.5 py-1.5 text-sm font-bold' 
    : 'px-2.5 py-1 text-xs font-bold';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${current.bg} ${sizeClasses} tracking-wide font-mono shadow-sm backdrop-blur-sm`}>
      <span className={`w-1.5 h-1.5 rounded-full ${current.dot}`}></span>
      <Icon className="w-3.5 h-3.5" />
      <span>{current.label}</span>
    </span>
  );
}
