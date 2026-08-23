import React from 'react';
import { 
  Home as HomeIcon, 
  FileText, 
  MessageSquareCode, 
  Search, 
  Shield, 
  Sparkles,
  PhoneCall,
  RotateCcw,
  CheckCircle2,
  Layers
} from 'lucide-react';
import { useComplaints } from '../context/ComplaintContext';

export default function Sidebar({ activePage, setActivePage }) {
  const { complaints, resetToDemo } = useComplaints();
  const criticalCount = complaints.filter(c => c.priority === 'CRITICAL' && c.status !== 'CLOSED').length;
  const openCount = complaints.filter(c => c.status !== 'CLOSED').length;

  const navItems = [
    { id: 'home', label: 'Home', icon: HomeIcon, desc: 'Overview & Citizen Services' },
    { id: 'report', label: 'Report Issue', icon: FileText, desc: 'Structured Triage Intake' },
    { id: 'chat', label: 'AI Chat', icon: MessageSquareCode, desc: 'Conversational Assistant' },
    { id: 'track', label: 'Track Petition', icon: Search, desc: 'Live Audit & Timeline' },
    { id: 'authority', label: 'Authority Command', icon: Shield, count: criticalCount, desc: 'Officer Dispatch Desk' },
  ];

  return (
    <aside className="hidden md:flex flex-col w-64 lg:w-72 shrink-0 bg-white border-r border-slate-200 min-h-[calc(100vh-105px)] sticky top-[105px] py-6 px-4 space-y-6 shadow-sm">
      {/* Navigation Label */}
      <div className="px-2">
        <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-slate-400 block">
          Navigation Menu
        </span>
      </div>

      {/* Vertical Navigation Items */}
      <nav className="space-y-1.5 flex-1">
        {navItems.map((item) => {
          const isActive = activePage === item.id;
          const Icon = item.icon;

          return (
            <button
              key={item.id}
              onClick={() => setActivePage(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-3 rounded-2xl text-left transition-all group ${
                isActive
                  ? 'bg-red-50 text-red-700 font-extrabold border-l-4 border-red-600 shadow-sm'
                  : 'text-slate-700 hover:bg-slate-100/80 hover:text-red-700 border-l-4 border-transparent hover:border-red-400 font-semibold'
              }`}
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className={`p-2 rounded-xl transition-colors ${
                  isActive 
                    ? 'bg-red-600 text-white shadow-sm' 
                    : 'bg-slate-100 text-slate-600 group-hover:bg-red-100 group-hover:text-red-600'
                }`}>
                  <Icon className="w-4 h-4 shrink-0" />
                </div>
                <div className="truncate">
                  <div className="text-xs font-bold leading-tight">{item.label}</div>
                  <div className={`text-[10px] leading-tight truncate ${isActive ? 'text-red-600/80' : 'text-slate-400'}`}>
                    {item.desc}
                  </div>
                </div>
              </div>

              {item.count > 0 && (
                <span className="ml-2 text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-red-100 text-red-700 border border-red-300 animate-pulse shrink-0">
                  {item.count}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Quick Statistics Mini Card */}
      <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2.5">
        <div className="flex items-center justify-between text-xs">
          <span className="font-bold text-slate-700 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-red-600" />
            <span>Active Queue</span>
          </span>
          <span className="font-mono font-black text-red-600 bg-red-100 px-2 py-0.5 rounded-md text-[11px]">
            {openCount} Open
          </span>
        </div>
        <div className="text-[11px] text-slate-500 font-medium leading-relaxed">
          AI Triage & Deterministic Risk Dispatch Engine active across all wards.
        </div>
      </div>

      {/* Emergency Helpline Box */}
      <div className="p-3.5 rounded-2xl bg-red-50 border border-red-200 text-red-900 space-y-1 text-xs">
        <div className="flex items-center gap-1.5 font-bold">
          <PhoneCall className="w-3.5 h-3.5 text-red-600" />
          <span>Toll-Free Helplines</span>
        </div>
        <div className="text-[11px] text-red-800 font-mono font-semibold pt-0.5 space-y-0.5">
          <div>Emergency: <strong>112</strong></div>
          <div>Civic Grievance: <strong>1916</strong></div>
        </div>
      </div>
    </aside>
  );
}
