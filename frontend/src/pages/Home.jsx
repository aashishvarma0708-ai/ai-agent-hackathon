import React, { useState } from 'react';
import { 
  FileText, 
  MessageSquareCode, 
  ArrowRight, 
  Sparkles, 
  Search, 
  Layers, 
  Cpu, 
  ExternalLink,
  ChevronRight,
  Building2,
  ShieldCheck,
  PlusCircle
} from 'lucide-react';
import CivicStatsBanner from '../components/CivicStatsBanner';
import HotspotMap from '../components/HotspotMap';
import { useComplaints } from '../context/ComplaintContext';

export default function Home({ setActivePage, setTrackSearchId }) {
  const [homeSearchInput, setHomeSearchInput] = useState('');
  const { complaints } = useComplaints();

  const handleTrackSubmit = (e) => {
    e.preventDefault();
    if (homeSearchInput.trim()) {
      setTrackSearchId(homeSearchInput.trim().toUpperCase());
      setActivePage('track');
    }
  };

  return (
    <div className="space-y-12 py-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* 1. TOP SECTION: Citizen Services with Hero "Report an Issue" & 4 Service Boxes */}
      <section className="space-y-8 pt-2">
        {/* Hero Spotlight: Report an Issue */}
        <div className="relative overflow-hidden rounded-3xl bg-white border border-slate-200/90 p-8 sm:p-10 shadow-lg">
          <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-red-500/10 via-amber-500/5 to-transparent rounded-full blur-3xl pointer-events-none"></div>
          <div className="relative z-10 max-w-3xl space-y-4">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-red-50 border border-red-200 text-red-700 text-xs font-bold">
              <Sparkles className="w-3.5 h-3.5 text-red-600 animate-spin" />
              <span>Official Public Redressal & Civic Governance Portal</span>
            </div>
            
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight text-[#162044] leading-tight">
              Report an Issue in Your Ward. <br />
              <span className="text-[#e53935]">
                Fast, Multimodal & Guaranteed Action.
              </span>
            </h1>

            <p className="text-sm sm:text-base text-slate-600 font-medium leading-relaxed max-w-2xl">
              Submit grievances with instant photo upload, AI landmark detection, and zero-hallucination routing to municipal departments.
            </p>

            <div className="pt-2 flex flex-wrap items-center gap-3">
              <button
                onClick={() => setActivePage('report')}
                className="px-6 py-3.5 rounded-2xl bg-[#e53935] hover:bg-[#d32f2f] text-white font-extrabold text-sm shadow-xl shadow-red-500/25 transition-all hover:scale-105 active:scale-95 flex items-center gap-2"
              >
                <PlusCircle className="w-5 h-5" />
                <span>Report Issue Now</span>
              </button>

              <button
                onClick={() => setActivePage('chat')}
                className="px-5 py-3.5 rounded-2xl bg-[#162044] hover:bg-[#0f1730] text-white font-bold text-sm shadow-md transition-all flex items-center gap-2"
              >
                <MessageSquareCode className="w-5 h-5 text-amber-400" />
                <span>Chat with AI Assistant</span>
              </button>
            </div>
          </div>
        </div>

        {/* Citizen Services Header & 4-Box Grid (Exact Reference Design System) */}
        <div className="space-y-6">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl sm:text-3xl font-black text-[#162044] tracking-tight flex items-center gap-2">
                Citizen Services
              </h2>
              <span className="text-xs font-mono font-bold text-slate-500">
                Direct Access Portal
              </span>
            </div>
            {/* Distinctive Red Underline Accent from Reference */}
            <div className="w-16 h-1 bg-[#e53935] rounded-full shadow-sm shadow-red-500/40"></div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* Card 1: Search Petition & Track (Soft Yellow/Amber) */}
            <div 
              onClick={() => setActivePage('track')}
              className="group relative bg-[#fef8d8] hover:bg-[#fff9db] border border-[#fde68a] hover:border-amber-400 rounded-3xl p-6 flex flex-col items-center text-center cursor-pointer transition-all duration-300 transform hover:-translate-y-2 hover:shadow-xl hover:shadow-amber-200/80 overflow-hidden"
            >
              <div className="w-16 h-16 rounded-2xl bg-[#fef08a] border border-[#fde047] flex items-center justify-center mb-4 group-hover:scale-110 group-hover:rotate-3 transition-transform duration-300 shadow-sm">
                <Search className="w-8 h-8 text-amber-800" />
              </div>
              <h3 className="text-base font-extrabold text-slate-900 group-hover:text-amber-900 transition-colors">
                Search Petition & Track
              </h3>
              <p className="mt-2 text-xs text-slate-600 leading-relaxed line-clamp-2">
                Real-time progress check and timeline audit for registered grievances.
              </p>
              <div className="mt-4 pt-3 border-t border-amber-200/60 w-full flex items-center justify-center gap-1.5 text-xs font-bold text-amber-800 group-hover:translate-x-1 transition-transform">
                <span>Track Grievance</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </div>
            </div>

            {/* Card 2: Submit A Complaint (Soft Lavender/Purple) */}
            <div 
              onClick={() => setActivePage('report')}
              className="group relative bg-[#ece8fc] hover:bg-[#f0ecff] border border-[#ddd6fe] hover:border-purple-400 rounded-3xl p-6 flex flex-col items-center text-center cursor-pointer transition-all duration-300 transform hover:-translate-y-2 hover:shadow-xl hover:shadow-purple-200/80 overflow-hidden"
            >
              <div className="w-16 h-16 rounded-2xl bg-[#ddd6fe] border border-[#c4b5fd] flex items-center justify-center mb-4 group-hover:scale-110 group-hover:-3deg transition-transform duration-300 shadow-sm">
                <FileText className="w-8 h-8 text-purple-800" />
              </div>
              <h3 className="text-base font-extrabold text-slate-900 group-hover:text-purple-900 transition-colors">
                Submit A Complaint
              </h3>
              <p className="mt-2 text-xs text-slate-600 leading-relaxed line-clamp-2">
                Structured form with category selector, landmark locator & photo upload.
              </p>
              <div className="mt-4 pt-3 border-t border-purple-200/60 w-full flex items-center justify-center gap-1.5 text-xs font-bold text-purple-800 group-hover:translate-x-1 transition-transform">
                <span>Open Intake Form</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </div>
            </div>

            {/* Card 3: Conversational AI Chat (Soft Sky/Cyan) */}
            <div 
              onClick={() => setActivePage('chat')}
              className="group relative bg-[#e0f4fc] hover:bg-[#e6f7fd] border border-[#bae6fd] hover:border-sky-400 rounded-3xl p-6 flex flex-col items-center text-center cursor-pointer transition-all duration-300 transform hover:-translate-y-2 hover:shadow-xl hover:shadow-sky-200/80 overflow-hidden"
            >
              <div className="w-16 h-16 rounded-2xl bg-[#bae6fd] border border-[#7dd3fc] flex items-center justify-center mb-4 group-hover:scale-110 group-hover:rotate-3 transition-transform duration-300 shadow-sm">
                <MessageSquareCode className="w-8 h-8 text-sky-800" />
              </div>
              <h3 className="text-base font-extrabold text-slate-900 group-hover:text-sky-900 transition-colors">
                Conversational AI Chat
              </h3>
              <p className="mt-2 text-xs text-slate-600 leading-relaxed line-clamp-2">
                Chat naturally for automated entity extraction & instant AI dispatch.
              </p>
              <div className="mt-4 pt-3 border-t border-sky-200/60 w-full flex items-center justify-center gap-1.5 text-xs font-bold text-sky-800 group-hover:translate-x-1 transition-transform">
                <span>Start AI Chat</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </div>
            </div>

            {/* Card 4: Authority Command Center (Soft Mint/Emerald) */}
            <div 
              onClick={() => setActivePage('authority')}
              className="group relative bg-[#e6f9f0] hover:bg-[#ebfbf3] border border-[#a7f3d0] hover:border-emerald-400 rounded-3xl p-6 flex flex-col items-center text-center cursor-pointer transition-all duration-300 transform hover:-translate-y-2 hover:shadow-xl hover:shadow-emerald-200/80 overflow-hidden"
            >
              <div className="w-16 h-16 rounded-2xl bg-[#a7f3d0] border border-[#6ee7b7] flex items-center justify-center mb-4 group-hover:scale-110 group-hover:-3deg transition-transform duration-300 shadow-sm">
                <ShieldCheck className="w-8 h-8 text-emerald-800" />
              </div>
              <h3 className="text-base font-extrabold text-slate-900 group-hover:text-emerald-900 transition-colors">
                Authority Command
              </h3>
              <p className="mt-2 text-xs text-slate-600 leading-relaxed line-clamp-2">
                Official operations desk for municipal field crews & resolution audit.
              </p>
              <div className="mt-4 pt-3 border-t border-emerald-200/60 w-full flex items-center justify-center gap-1.5 text-xs font-bold text-emerald-800 group-hover:translate-x-1 transition-transform">
                <span>Access Command</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. SECOND SECTION: Next-Gen Municipal AI Architecture & Triage Showcase */}
      <section className="relative bg-white border border-slate-200 shadow-sm rounded-3xl p-8 sm:p-10">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-red-50 border border-red-200 text-red-700 text-xs font-bold mb-6">
          <Sparkles className="w-3.5 h-3.5 text-red-600 animate-spin" />
          <span>Next-Gen Municipal AI & Public Service Triage</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-7 space-y-6">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight text-[#162044] leading-[1.1]">
              Intelligent civic reporting. <br className="hidden sm:block" />
              <span className="text-[#e53935]">
                Guaranteed accountability.
              </span>
            </h2>

            <p className="text-base sm:text-lg text-slate-700 font-semibold max-w-2xl leading-relaxed border-l-4 border-red-500 pl-4 py-1">
              "One place to report. Intelligence to route. Accountability until resolution."
            </p>

            <p className="text-sm text-slate-600 max-w-xl">
              CivicResolve AI understands multimodal citizen complaints in any language, scores real public safety risk deterministically, routes issues to the right municipal department without human delays, and prevents hallucinations.
            </p>

            {/* Quick Track Input Bar */}
            <form onSubmit={handleTrackSubmit} className="pt-2 flex flex-col sm:flex-row items-center gap-2.5 max-w-lg">
              <div className="relative w-full">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Enter Complaint ID (e.g. CR-260820-1042)"
                  value={homeSearchInput}
                  onChange={(e) => setHomeSearchInput(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-300 rounded-xl text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-red-500 focus:bg-white font-mono shadow-inner transition-all"
                />
              </div>
              <button
                type="submit"
                className="w-full sm:w-auto px-5 py-3 rounded-xl bg-[#162044] hover:bg-[#0f1730] text-xs sm:text-sm font-bold text-white shrink-0 transition-all flex items-center justify-center gap-2 shadow-sm"
              >
                <span>Track Ticket</span>
                <ArrowRight className="w-4 h-4 text-amber-400" />
              </button>
            </form>
          </div>

          {/* Hero Visual Card / Triage Card */}
          <div className="lg:col-span-5">
            <div className="bg-slate-50 p-6 rounded-3xl border border-slate-200 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                <div className="flex items-center gap-2.5">
                  <div className="w-3 h-3 rounded-full bg-red-500 animate-ping"></div>
                  <span className="text-xs font-bold text-slate-800 uppercase tracking-wider font-mono">
                    Live AI Triage Engine
                  </span>
                </div>
                <span className="text-[11px] font-mono text-red-700 bg-red-100 px-2 py-0.5 rounded border border-red-200 font-bold">
                  Zero Hallucination
                </span>
              </div>

              <div className="mt-4 space-y-3.5 text-xs">
                <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Citizen Input (Multimodal)</span>
                  <p className="text-slate-800 italic">"Pothole outside St. Mary's School. Two bikes skidded this morning during drop-off."</p>
                </div>

                <div className="grid grid-cols-2 gap-2 font-mono">
                  <div className="bg-white p-2.5 rounded-lg border border-slate-200 shadow-sm">
                    <span className="text-[10px] text-slate-500 block font-sans">Domain</span>
                    <span className="text-emerald-700 font-black">MUNICIPAL</span>
                  </div>
                  <div className="bg-white p-2.5 rounded-lg border border-slate-200 shadow-sm">
                    <span className="text-[10px] text-slate-500 block font-sans">Category</span>
                    <span className="text-slate-800 font-bold">ROADS & SAFETY</span>
                  </div>
                  <div className="bg-white p-2.5 rounded-lg border border-slate-200 shadow-sm">
                    <span className="text-[10px] text-slate-500 block font-sans">Deterministic Risk</span>
                    <span className="text-red-600 font-black">88/100 (CRITICAL)</span>
                  </div>
                  <div className="bg-white p-2.5 rounded-lg border border-slate-200 shadow-sm">
                    <span className="text-[10px] text-slate-500 block font-sans">SLA Commitment</span>
                    <span className="text-blue-700 font-bold">24 Hours</span>
                  </div>
                </div>

                <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-emerald-600" />
                    <span className="text-slate-800 font-bold text-[11px]">Roads & Infrastructure Dept</span>
                  </div>
                  <span className="text-[10px] font-mono bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded">
                    Auto-Dispatched
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Live Stats Ticker */}
      <CivicStatsBanner />

      {/* Live Hotspot Map Section */}
      <section className="space-y-4 bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-xl sm:text-2xl font-black text-[#162044] flex items-center gap-2">
              <Layers className="w-5 h-5 text-red-600" />
              <span>Real-Time Civic Hotspot Radar</span>
            </h2>
            <p className="text-xs text-slate-600 font-medium">
              Interactive geographic cluster visualization showing active risk clusters across city wards.
            </p>
          </div>
          <button
            onClick={() => setActivePage('authority')}
            className="text-xs font-bold text-red-600 hover:text-red-700 flex items-center gap-1.5"
          >
            <span>Open Authority Dashboard</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        <HotspotMap 
          complaints={complaints}
          onSelectComplaint={(id) => {
            setTrackSearchId(id);
            setActivePage('track');
          }}
        />
      </section>

      {/* Architecture Principle Explainer */}
      <section className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
        <div className="max-w-3xl mb-8">
          <div className="flex items-center gap-2 text-xs font-mono text-red-600 uppercase font-bold mb-2">
            <Cpu className="w-4 h-4" />
            <span>Architecture Principle</span>
          </div>
          <h2 className="text-2xl font-black text-[#162044]">
            AI interprets. Python enforces. Tools act.
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 mt-2 font-medium">
            Unlike naive chatbots that hallucinate department contacts or fake resolutions, CivicResolve enforces strict separation of concerns.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="w-8 h-8 rounded-lg bg-sky-100 text-sky-800 flex items-center justify-center font-bold text-sm font-mono">
              01
            </div>
            <h4 className="text-sm font-black text-slate-900">1. AI Interprets</h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              Extracts structured facts from images, messy text descriptions, and multilingual audio recordings without bias.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-800 flex items-center justify-center font-bold text-sm font-mono">
              02
            </div>
            <h4 className="text-sm font-black text-slate-900">2. Python Enforces</h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              Determines immutable Ticket IDs, deterministic safety risk scores (0-100), SLA limits, and duplicate thresholds.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold text-sm font-mono">
              03
            </div>
            <h4 className="text-sm font-black text-slate-900">3. Tools Act</h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              Dispatches work orders to municipal crews or routes to verified national services (ERSS 112, NALSA, NCH) with audit logs.
            </p>
          </div>
        </div>
      </section>

      {/* Verified Fallback Directory */}
      <section className="space-y-6 bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-2xl font-black text-[#162044]">
            Verified Public Service Guardrails
          </h2>
          <p className="text-xs text-slate-600 mt-1 font-medium">
            When a citizen reports something outside municipal purview, CivicResolve never hallucinates — it routes directly to verified national services.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl bg-red-50/50 border border-red-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-900">Emergency (112)</span>
              <span className="text-[10px] font-mono bg-red-100 text-red-800 font-bold px-1.5 py-0.5 rounded">Police / Fire / Medical</span>
            </div>
            <p className="text-[11px] text-slate-600">
              Immediate threat to life or property triggers instant 112 emergency routing with zero wait time.
            </p>
            <a href="https://112.gov.in" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[11px] text-red-600 font-bold hover:underline">
              <span>View Portal</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="p-4 rounded-2xl bg-purple-50/50 border border-purple-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-900">Legal Aid (NALSA)</span>
              <span className="text-[10px] font-mono bg-purple-100 text-purple-800 font-bold px-1.5 py-0.5 rounded">Legal Redressal</span>
            </div>
            <p className="text-[11px] text-slate-600">
              Disputes and civil rights grievances routed directly to National Legal Services Authority.
            </p>
            <a href="https://nalsa.gov.in" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[11px] text-purple-600 font-bold hover:underline">
              <span>View Portal</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="p-4 rounded-2xl bg-blue-50/50 border border-blue-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-900">Consumer Helpline</span>
              <span className="text-[10px] font-mono bg-blue-100 text-blue-800 font-bold px-1.5 py-0.5 rounded">E-commerce / Fraud</span>
            </div>
            <p className="text-[11px] text-slate-600">
              Merchant scams and defective product claims routed directly to National Consumer Helpline.
            </p>
            <a href="https://consumerhelpline.gov.in" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[11px] text-blue-600 font-bold hover:underline">
              <span>View Portal</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="p-4 rounded-2xl bg-emerald-50/50 border border-emerald-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-900">Municipal Portal</span>
              <span className="text-[10px] font-mono bg-emerald-100 text-emerald-800 font-bold px-1.5 py-0.5 rounded">Civic Governance</span>
            </div>
            <p className="text-[11px] text-slate-600">
              Roads, drainage, solid waste, water supply, and streetlights routed to local municipal wards.
            </p>
            <button onClick={() => setActivePage('report')} className="inline-flex items-center gap-1 text-[11px] text-emerald-700 font-bold hover:underline">
              <span>Submit Issue</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
