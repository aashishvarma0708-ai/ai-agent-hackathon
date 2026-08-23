import React from 'react';
import { 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  RotateCcw, 
  ShieldCheck, 
  FileText, 
  UserCheck, 
  Wrench, 
  Sparkles,
  ArrowRight
} from 'lucide-react';

export const LIFECYCLE_STEPS = [
  { status: 'NEW', label: 'Complaint Received', icon: FileText },
  { status: 'ACKNOWLEDGED', label: 'Acknowledged', icon: Clock },
  { status: 'ASSIGNED', label: 'Assigned', icon: UserCheck },
  { status: 'WORK_STARTED', label: 'Work Started', icon: Wrench },
  { status: 'RESOLUTION_SUBMITTED', label: 'Resolution Submitted', icon: Sparkles },
  { status: 'AI_VERIFICATION_PENDING', label: 'AI Verification', icon: Sparkles },
  { status: 'RESOLVED_PENDING_CITIZEN', label: 'Citizen Confirmation', icon: ShieldCheck },
  { status: 'CLOSED', label: 'Closed', icon: CheckCircle2 }
];

export default function ComplaintLifecycle({ currentStatus = 'NEW', className = '' }) {
  const statusUpper = (currentStatus || 'NEW').toUpperCase();

  const getStepIndex = (status) => {
    switch (status) {
      case 'NEW': return 0;
      case 'ACKNOWLEDGED': return 1;
      case 'ASSIGNED': return 2;
      case 'WORK_STARTED': return 3;
      case 'RESOLUTION_SUBMITTED': return 4;
      case 'AI_VERIFICATION_PENDING': return 5;
      case 'RESOLVED_PENDING_CITIZEN': return 6;
      case 'CLOSED': return 7;
      case 'HUMAN_REVIEW_REQUIRED': return 5; // branch of verification
      case 'REOPENED': return 3; // return to corrective work
      default: return 0;
    }
  };

  const currentIndex = getStepIndex(statusUpper);
  const isHumanReview = statusUpper === 'HUMAN_REVIEW_REQUIRED';
  const isReopened = statusUpper === 'REOPENED';

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Special Case Alerts: HUMAN_REVIEW_REQUIRED or REOPENED */}
      {isHumanReview && (
        <div className="p-4 rounded-2xl bg-amber-50 border-2 border-amber-300 text-amber-900 flex items-start gap-3 shadow-xs">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <h4 className="text-xs font-black uppercase tracking-wider text-amber-900">
              Human Review Required
            </h4>
            <p className="text-xs text-amber-800 font-medium leading-relaxed">
              AI verification flagged resolution proof for human authority inspection. Review before/after photos to approve resolution or reopen the case.
            </p>
          </div>
        </div>
      )}

      {isReopened && (
        <div className="p-4 rounded-2xl bg-red-50 border-2 border-red-400 text-red-900 flex items-start gap-3 shadow-xs">
          <RotateCcw className="w-5 h-5 text-red-600 shrink-0 mt-0.5 animate-spin-reverse" />
          <div className="space-y-0.5">
            <h4 className="text-xs font-black uppercase tracking-wider text-red-900">
              Case Reopened — Corrective Work Required
            </h4>
            <p className="text-xs text-red-800 font-medium leading-relaxed">
              Resolution evidence was rejected by authority review or contested by citizen. Field crew must re-engage and provide new resolution evidence.
            </p>
          </div>
        </div>
      )}

      {/* Stepper Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
        {LIFECYCLE_STEPS.map((step, idx) => {
          const isPassed = idx < currentIndex || (idx === currentIndex && statusUpper === 'CLOSED');
          const isCurrent = idx === currentIndex && statusUpper !== 'CLOSED';
          const Icon = step.icon;

          let badgeBg = 'bg-slate-50/50 border-slate-200 text-slate-400';
          let iconColor = 'text-slate-400';
          let symbol = '○';

          if (isCurrent) {
            if (isReopened) {
              badgeBg = 'bg-red-50 border-red-400 text-red-700 font-bold shadow-sm ring-2 ring-red-400/20';
              iconColor = 'text-red-600';
              symbol = '●';
            } else if (isHumanReview) {
              badgeBg = 'bg-amber-50 border-amber-400 text-amber-800 font-bold shadow-sm ring-2 ring-amber-400/20';
              iconColor = 'text-amber-600';
              symbol = '●';
            } else {
              badgeBg = 'bg-red-50 border-red-300 text-red-700 font-bold shadow-sm ring-2 ring-red-400/20';
              iconColor = 'text-red-600';
              symbol = '●';
            }
          } else if (isPassed) {
            badgeBg = 'bg-white border-slate-300 text-slate-800 font-semibold shadow-xs';
            iconColor = 'text-emerald-600';
            symbol = '✓';
          }

          return (
            <div
              key={step.status}
              className={`p-2.5 rounded-2xl border transition-all flex flex-col justify-between h-20 ${badgeBg}`}
            >
              <div className="flex items-center justify-between text-xs">
                <Icon className={`w-3.5 h-3.5 ${iconColor}`} />
                <span className="font-mono text-[11px] font-bold">{symbol}</span>
              </div>
              <div>
                <span className="text-[9px] uppercase font-mono text-slate-400 block font-bold">Step {idx + 1}</span>
                <p className="text-[10px] font-bold leading-tight truncate" title={step.label}>
                  {step.label}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
