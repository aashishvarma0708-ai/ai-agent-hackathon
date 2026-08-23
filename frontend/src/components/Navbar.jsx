import React, { useState, useEffect } from 'react';
import { 
  PlusCircle, 
  Menu,
  X,
  PhoneCall,
  Clock,
  Globe,
  Shield
} from 'lucide-react';
import { useComplaints } from '../context/ComplaintContext';

const CALLBOT_NUMBER = import.meta.env.VITE_CALLBOT_NUMBER?.trim() || '';
const CALLBOT_TEL = CALLBOT_NUMBER.replace(/[^\d+]/g, '');

export default function Navbar({ activePage, setActivePage }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { complaints } = useComplaints();
  const [currentTime, setCurrentTime] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const options = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: true 
      };
      setCurrentTime(now.toLocaleDateString('en-IN', options));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const criticalCount = complaints.filter(c => c.priority === 'CRITICAL' && c.status !== 'CLOSED').length;

  const navItems = [
    { id: 'home', label: 'Home' },
    { id: 'report', label: 'Report Issue' },
    { id: 'chat', label: 'AI Chat' },
    { id: 'track', label: 'Track Petition' },
    { id: 'authority', label: 'Authority Command', count: criticalCount },
  ];

  return (
    <header className="sticky top-0 z-50 bg-white shadow-sm border-b border-slate-200">
      {/* Top Info & Callbot Strip */}
      <div className="flex flex-col sm:flex-row items-center justify-between text-[11px] font-medium border-b border-slate-100 bg-[#162044] text-white">
        {/* Red Helpline Banner with configured Callbot number */}
        {CALLBOT_NUMBER ? (
          <div className="bg-[#e53935] text-white px-4 py-1.5 flex items-center gap-2 font-bold w-full sm:w-auto justify-center sm:justify-start text-xs">
            <PhoneCall className="w-3.5 h-3.5 animate-pulse" />
            <span>CivicResolve AI Voice Agent:</span>
            <a href={`tel:${CALLBOT_TEL}`} className="underline hover:text-amber-200 transition-colors font-mono font-black">
              {CALLBOT_NUMBER}
            </a>
          </div>
        ) : (
          <div className="bg-[#e53935] text-white px-4 py-1.5 flex items-center gap-2 font-bold w-full sm:w-auto justify-center sm:justify-start text-xs">
            <Shield className="w-3.5 h-3.5" />
            <span>Official Public Grievance Redressal Portal</span>
          </div>
        )}

        {/* Live Date, Time & Language */}
        <div className="hidden sm:flex items-center gap-4 px-4 py-1.5 text-slate-200">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-slate-300" />
            <span className="font-mono text-[11px]">{currentTime || 'Saturday, 22 August 2026'}</span>
          </div>
          <span className="opacity-40">|</span>
          <div className="flex items-center gap-1 text-[11px] text-slate-300 hover:text-white cursor-pointer">
            <Globe className="w-3.5 h-3.5 text-slate-400" />
            <span>English ▾</span>
          </div>
        </div>
      </div>

      {/* Main Branding Bar */}
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-20">
          {/* Official Emblem & Portal Title */}
          <div 
            onClick={() => { setActivePage('home'); setMobileOpen(false); }}
            className="flex items-center gap-3.5 cursor-pointer select-none group"
          >
            <div className="w-11 h-11 sm:w-12 sm:h-12 rounded-xl bg-gradient-to-tr from-red-600 via-rose-500 to-amber-500 p-0.5 shadow-md shadow-red-500/20 group-hover:scale-105 transition-transform flex items-center justify-center">
              <div className="w-full h-full bg-white rounded-[10px] flex items-center justify-center">
                <span className="text-2xl">🏛️</span>
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-black text-xl sm:text-2xl tracking-tight text-[#162044]">
                  CivicResolve<span className="text-red-600">.ai</span>
                </span>
              </div>
              <p className="text-[10px] text-slate-500 font-semibold hidden sm:block">
                Municipal AI Triage & Public Grievance Redressal Desk
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="hidden md:flex items-center gap-2.5">
            <button
              onClick={() => setActivePage('report')}
              className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-xs transition-colors border border-slate-300 flex items-center gap-1.5 shadow-2xs"
            >
              <PlusCircle className="w-3.5 h-3.5 text-red-600" />
              <span>Report Issue</span>
            </button>

            <button
              onClick={() => setActivePage('authority')}
              className="px-4 py-2 rounded-xl bg-[#e53935] hover:bg-[#d32f2f] text-white font-bold text-xs shadow-md shadow-red-500/25 transition-all hover:scale-105 active:scale-95 flex items-center gap-1.5"
            >
              <Shield className="w-3.5 h-3.5" />
              <span>Authority Login</span>
            </button>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden items-center gap-2">
            <button
              onClick={() => setActivePage('report')}
              className="p-2 rounded-lg bg-[#e53935] text-white font-bold text-xs"
            >
              <PlusCircle className="w-4 h-4" />
            </button>
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="p-2 text-slate-700 hover:text-slate-900 rounded-lg hover:bg-slate-100"
            >
              {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileOpen && (
        <div className="md:hidden border-b border-slate-200 bg-white px-4 pt-2 pb-4 space-y-1 shadow-lg">
          {navItems.map((item) => {
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActivePage(item.id);
                  setMobileOpen(false);
                }}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-bold ${
                  isActive ? 'bg-red-50 text-red-600 border-l-4 border-red-600' : 'text-slate-700 hover:bg-slate-50'
                }`}
              >
                <span>{item.label}</span>
                {item.count > 0 && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-red-100 text-red-700">
                    {item.count}
                  </span>
                )}
              </button>
            );
          })}
          <div className="pt-2 border-t border-slate-200 flex flex-col gap-2">
            <button
              onClick={() => { setActivePage('authority'); setMobileOpen(false); }}
              className="w-full py-2 bg-red-600 text-white rounded-xl text-xs font-bold text-center"
            >
              Authority Login
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
