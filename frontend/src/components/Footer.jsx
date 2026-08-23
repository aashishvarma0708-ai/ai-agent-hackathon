import React from 'react';
import { Shield, ExternalLink, Cpu } from 'lucide-react';

export default function Footer({ setActivePage }) {
  return (
    <footer className="mt-20 border-t-4 border-[#e53935] bg-[#101730] text-slate-300 pt-12 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 pb-10 border-b border-slate-800">
          {/* Brand Column */}
          <div className="space-y-3 md:col-span-2">
            <div className="flex items-center gap-2">
              <span className="text-2xl">🏛️</span>
              <span className="font-black text-xl tracking-tight text-white">
                CivicResolve<span className="text-red-500">.ai</span>
              </span>
              <span className="text-[10px] uppercase font-mono font-bold bg-red-900/50 text-red-300 px-2 py-0.5 rounded border border-red-700">
                Government Edition
              </span>
            </div>
            <p className="text-sm font-semibold text-amber-300 italic">
              "One place to report. Intelligence to route. Accountability until resolution."
            </p>
            <p className="text-xs text-slate-400 max-w-md leading-relaxed">
              CivicResolve AI bridges the gap between citizens and municipal authorities with multimodal AI triage, deterministic risk scoring, transparent agent audit logs, and zero-hallucination public routing.
            </p>
            <div className="flex items-center gap-2 pt-2 text-[11px] text-slate-400">
              <Cpu className="w-3.5 h-3.5 text-amber-400" />
              <span>Architecture Principle: <strong>AI interprets. Python enforces. Tools act.</strong></span>
            </div>
          </div>

          {/* Quick Pathways */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-100 mb-3">
              Citizen Reporting
            </h4>
            <ul className="space-y-2 text-xs text-slate-400">
              <li>
                <button onClick={() => setActivePage('report')} className="hover:text-red-400 transition-colors">
                  • Submit A Complaint
                </button>
              </li>
              <li>
                <button onClick={() => setActivePage('chat')} className="hover:text-red-400 transition-colors">
                  • Conversational AI Assistant
                </button>
              </li>
              <li>
                <button onClick={() => setActivePage('track')} className="hover:text-red-400 transition-colors">
                  • Search Petition & Track
                </button>
              </li>
              <li>
                <button onClick={() => setActivePage('authority')} className="hover:text-red-400 transition-colors">
                  • Authority Command Center
                </button>
              </li>
            </ul>
          </div>

          {/* Verified Directory Notice */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-100 mb-3 flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-red-400" />
              Verified Directory
            </h4>
            <p className="text-[11px] text-slate-400 leading-relaxed mb-3">
              External emergency, legal, and consumer links are strictly controlled by a verified national directory. The AI never invents government helpline numbers.
            </p>
            <div className="flex flex-col gap-1.5 text-[11px]">
              <a href="https://112.gov.in" target="_blank" rel="noreferrer" className="text-red-400 hover:underline flex items-center gap-1">
                <ExternalLink className="w-3 h-3" /> ERSS 112 National Emergency
              </a>
              <a href="https://nalsa.gov.in" target="_blank" rel="noreferrer" className="text-purple-400 hover:underline flex items-center gap-1">
                <ExternalLink className="w-3 h-3" /> NALSA Free Legal Aid
              </a>
              <a href="https://consumerhelpline.gov.in" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline flex items-center gap-1">
                <ExternalLink className="w-3 h-3" /> National Consumer Helpline
              </a>
            </div>
          </div>
        </div>

        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-3">
          <p>© 2026 CivicResolve AI. Andhra Pradesh Public Grievance Portal.</p>
          <div className="flex items-center gap-4 text-[11px]">
            <span>FastAPI & AI Backend Ready</span>
            <span>•</span>
            <span>Vite + React Modern Frontend</span>
            <span>•</span>
            <span>Deterministic Triage Engine</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
