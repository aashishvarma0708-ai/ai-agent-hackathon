import React from 'react';
import { 
  Sparkles, 
  Eye, 
  UserCheck, 
  Wrench, 
  CheckCircle, 
  CheckCheck, 
  ExternalLink,
  Siren,
  RotateCcw
} from 'lucide-react';

export default function StatusBadge({ status = 'NEW', size = 'md' }) {
  const s = (status || 'NEW').toUpperCase();

  const configs = {
    NEW: {
      bg: 'bg-indigo-500/15 border-indigo-500/30 text-indigo-300',
      icon: Sparkles,
      label: 'NEW INTAKE',
    },
    ACKNOWLEDGED: {
      bg: 'bg-cyan-500/15 border-cyan-500/30 text-cyan-300',
      icon: Eye,
      label: 'ACKNOWLEDGED',
    },
    ASSIGNED: {
      bg: 'bg-sky-500/15 border-sky-500/30 text-sky-300',
      icon: UserCheck,
      label: 'CREW ASSIGNED',
    },
    WORK_STARTED: {
      bg: 'bg-amber-500/15 border-amber-500/30 text-amber-300',
      icon: Wrench,
      label: 'WORK IN PROGRESS',
    },
    RESOLUTION_SUBMITTED: {
      bg: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300',
      icon: CheckCircle,
      label: 'RESOLUTION SUBMITTED',
    },
    AI_VERIFICATION_PENDING: {
      bg: 'bg-cyan-500/15 border-cyan-500/30 text-cyan-300',
      icon: Sparkles,
      label: 'AI VERIFIED',
    },
    RESOLVED_PENDING_CITIZEN: {
      bg: 'bg-teal-500/15 border-teal-500/30 text-teal-300',
      icon: CheckCircle,
      label: 'RESOLVED (CITIZEN REVIEW)',
    },
    HUMAN_REVIEW_REQUIRED: {
      bg: 'bg-amber-500/15 border-amber-500/30 text-amber-300',
      icon: Eye,
      label: 'HUMAN REVIEW REQUIRED',
    },
    CLOSED: {
      bg: 'bg-slate-500/20 border-slate-500/30 text-slate-300',
      icon: CheckCheck,
      label: 'CLOSED',
    },
    REOPENED: {
      bg: 'bg-rose-500/15 border-rose-500/30 text-rose-300',
      icon: RotateCcw,
      label: 'REOPENED',
    },
    EXTERNALLY_ROUTED: {
      bg: 'bg-purple-500/15 border-purple-500/30 text-purple-300',
      icon: ExternalLink,
      label: 'EXTERNALLY ROUTED',
    },
    EMERGENCY_DISPATCHED: {
      bg: 'bg-red-500/20 border-red-500/40 text-red-300 animate-pulse',
      icon: Siren,
      label: '112 DISPATCHED',
    }
  };

  const current = configs[s] || {
    bg: 'bg-slate-500/20 border-slate-500/30 text-slate-300',
    icon: Sparkles,
    label: s.replace(/_/g, ' '),
  };

  const Icon = current.icon;
  const sizeClasses = size === 'sm' 
    ? 'px-2 py-0.5 text-xs font-semibold' 
    : size === 'lg' 
    ? 'px-3.5 py-1.5 text-sm font-bold' 
    : 'px-2.5 py-1 text-xs font-semibold';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${current.bg} ${sizeClasses} tracking-wide font-mono`}>
      <Icon className="w-3.5 h-3.5" />
      <span>{current.label}</span>
    </span>
  );
}
