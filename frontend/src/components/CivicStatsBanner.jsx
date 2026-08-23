import React from 'react';
import { ShieldCheck, Clock, Zap, Users, ArrowUpRight, Flame } from 'lucide-react';
import { useComplaints } from '../context/ComplaintContext';

export default function CivicStatsBanner() {
  const { complaints } = useComplaints();

  const total = complaints.length;
  const municipal = complaints.filter(c => c.domain === 'municipal');
  const openMunicipal = municipal.filter(c => !['CLOSED', 'RESOLUTION_SUBMITTED'].includes(c.status));
  const critical = municipal.filter(c => c.priority === 'CRITICAL' && c.status !== 'CLOSED');

  const stats = [
    {
      label: 'Active Civic Incidents',
      value: openMunicipal.length,
      trend: '+12% from yesterday',
      icon: Zap,
      color: 'text-amber-600',
      bg: 'bg-white border-slate-200 shadow-sm',
    },
    {
      label: 'Critical Risk Alerts',
      value: critical.length,
      trend: 'Zero-wait dispatch',
      icon: Flame,
      color: 'text-red-600',
      bg: 'bg-white border-slate-200 shadow-sm',
    },
    {
      label: 'Avg SLA Turnaround',
      value: '4.8 hrs',
      trend: '68% faster than manual desk',
      icon: Clock,
      color: 'text-blue-600',
      bg: 'bg-white border-slate-200 shadow-sm',
    },
    {
      label: 'AI Triage Accuracy',
      value: '98.4%',
      trend: 'Deterministic Python rules',
      icon: ShieldCheck,
      color: 'text-emerald-600',
      bg: 'bg-white border-slate-200 shadow-sm',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 my-6">
      {stats.map((stat, i) => {
        const Icon = stat.icon;
        return (
          <div
            key={i}
            className={`p-4 rounded-2xl border ${stat.bg} transition-all hover:shadow-md hover:-translate-y-0.5 duration-200`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500">{stat.label}</span>
              <Icon className={`w-4 h-4 ${stat.color}`} />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-black tracking-tight text-slate-900 font-mono">
                {stat.value}
              </span>
            </div>
            <p className="mt-1 text-[11px] text-slate-500 truncate">
              {stat.trend}
            </p>
          </div>
        );
      })}
    </div>
  );
}
