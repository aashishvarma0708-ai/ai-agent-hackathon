import React from 'react';
import { Terminal, CheckCircle2, ChevronRight, Cpu, ShieldCheck } from 'lucide-react';

export default function AgentTraceViewer({ trace = [] }) {
  if (!trace || trace.length === 0) return null;

  return (
    <div className="rounded-xl bg-slate-900/90 border border-slate-700/80 p-4 font-mono text-xs shadow-xl">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
        <div className="flex items-center gap-2 text-civic-400 font-semibold">
          <Cpu className="w-4 h-4 text-civic-400 animate-pulse" />
          <span>Agent Activity & Decision Trace</span>
        </div>
        <span className="text-[10px] text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
          Deterministic Rule Engine
        </span>
      </div>

      <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
        {trace.map((step, idx) => {
          const isAi = step.includes('AI') || step.includes('Multimodal') || step.includes('Parser');
          const isRisk = step.includes('Risk') || step.includes('score');
          const isRoute = step.includes('Routing') || step.includes('Department') || step.includes('Service');
          const isGuardrail = step.includes('Guardrail') || step.includes('Separation') || step.includes('Prevented');

          let badgeColor = 'text-slate-300';
          let borderAccent = 'border-slate-800';

          if (isGuardrail) {
            badgeColor = 'text-purple-300 bg-purple-950/40 border-purple-800/60';
          } else if (isAi) {
            badgeColor = 'text-cyan-300 bg-cyan-950/40 border-cyan-800/60';
          } else if (isRisk) {
            badgeColor = 'text-amber-300 bg-amber-950/40 border-amber-800/60';
          } else if (isRoute) {
            badgeColor = 'text-civic-300 bg-civic-950/40 border-civic-800/60';
          }

          return (
            <div 
              key={idx} 
              className={`flex items-start gap-2 p-2 rounded-lg bg-slate-950/70 border ${borderAccent} text-slate-200 transition-all hover:bg-slate-850`}
            >
              <div className="mt-0.5 text-civic-400 shrink-0 font-bold">
                {idx + 1}.
              </div>
              <div className="flex-1 leading-relaxed">
                {step}
              </div>
              <CheckCircle2 className="w-3.5 h-3.5 text-civic-500 shrink-0 mt-0.5" />
            </div>
          );
        })}
      </div>
    </div>
  );
}
