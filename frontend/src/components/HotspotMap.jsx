import React, { useState } from 'react';
import { MapPin, Layers, Navigation, Users, ShieldCheck, AlertTriangle } from 'lucide-react';
import PriorityBadge from './PriorityBadge';
import StatusBadge from './StatusBadge';

const ACTIVE_STATUSES = [
  'NEW',
  'ACKNOWLEDGED',
  'ASSIGNED',
  'WORK_STARTED',
  'RESOLUTION_SUBMITTED',
  'AI_VERIFICATION_PENDING',
  'HUMAN_REVIEW_REQUIRED',
  'RESOLVED_PENDING_CITIZEN',
  'REOPENED'
];

const hasValidCoordinates = (complaint) => {
  if (!complaint) return false;
  const lat = Number(complaint.latitude);
  const lng = Number(complaint.longitude);

  return (
    Number.isFinite(lat) &&
    Number.isFinite(lng) &&
    lat >= -90 &&
    lat <= 90 &&
    lng >= -180 &&
    lng <= 180
  );
};

export default function HotspotMap({ complaints = [], onSelectComplaint = () => {} }) {
  const [activeCategory, setActiveCategory] = useState('ALL');
  const [selectedPin, setSelectedPin] = useState(null);

  // Filter complaints: ONLY real complaints with valid numeric lat/lng and ACTIVE status
  const validActiveComplaints = complaints.filter(c => 
    hasValidCoordinates(c) &&
    ACTIVE_STATUSES.includes(c.status)
  );

  const filteredMarkers = activeCategory === 'ALL' 
    ? validActiveComplaints 
    : validActiveComplaints.filter(c => {
        const cat = (c.category || c.service_type || '').toLowerCase();
        return cat.includes(activeCategory.toLowerCase());
      });

  // Calculate dynamic bounding box
  const lats = filteredMarkers.map(c => Number(c.latitude));
  const lngs = filteredMarkers.map(c => Number(c.longitude));
  const minLat = lats.length ? Math.min(...lats) : 0;
  const maxLat = lats.length ? Math.max(...lats) : 0;
  const minLng = lngs.length ? Math.min(...lngs) : 0;
  const maxLng = lngs.length ? Math.max(...lngs) : 0;

  const latRange = maxLat - minLat;
  const lngRange = maxLng - minLng;
  const pad = 16; // Percentage padding inside the map canvas

  return (
    <div className="relative rounded-2xl overflow-hidden border border-slate-700/80 bg-slate-900 shadow-2xl">
      {/* Map Header / Controls */}
      <div className="absolute top-4 left-4 right-4 z-20 flex flex-wrap items-center justify-between gap-3 pointer-events-auto">
        <div className="flex items-center gap-2 bg-slate-900/90 backdrop-blur-md px-3.5 py-1.5 rounded-xl border border-slate-700 shadow-lg text-xs font-semibold text-slate-200">
          <Layers className="w-4 h-4 text-red-500" />
          <span>Civic Hotspot GIS Matrix</span>
          <span className="bg-red-500/20 text-red-300 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold">
            {filteredMarkers.length} Active Verified GPS
          </span>
        </div>

        <div className="flex items-center gap-1.5 bg-slate-900/90 backdrop-blur-md p-1 rounded-xl border border-slate-700 shadow-lg overflow-x-auto max-w-full">
          {['ALL', 'roads', 'water', 'garbage', 'drainage', 'streetlights'].map(cat => (
            <button
              key={cat}
              onClick={() => {
                setActiveCategory(cat);
                setSelectedPin(null);
              }}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all shrink-0 ${
                activeCategory === cat 
                  ? 'bg-red-600 text-white font-bold shadow-md' 
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              {cat === 'ALL' ? 'All Categories' : cat.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Stylized Interactive Map Canvas */}
      <div className="relative w-full h-[420px] bg-slate-950/90 overflow-hidden bg-grid-pattern flex items-center justify-center select-none">
        {/* Radar Scanner Effect */}
        <div className="absolute w-96 h-96 rounded-full border border-red-500/20 animate-pulse-slow pointer-events-none"></div>
        <div className="absolute w-[580px] h-[580px] rounded-full border border-slate-800/80 pointer-events-none"></div>
        <div className="absolute w-[780px] h-[780px] rounded-full border border-slate-800/40 pointer-events-none"></div>

        {/* Ward Boundaries Decorative Vector Lines */}
        <svg className="absolute inset-0 w-full h-full opacity-30 pointer-events-none">
          <path d="M 50 100 Q 200 150 350 120 T 700 200 T 1100 150" fill="none" stroke="#e53935" strokeWidth="1.5" strokeDasharray="6,6" />
          <path d="M 120 380 Q 400 300 650 340 T 1000 280" fill="none" stroke="#6366f1" strokeWidth="1" strokeDasharray="4,4" />
          <path d="M 300 20 L 450 220 L 320 380" fill="none" stroke="#0ea5e9" strokeWidth="1" strokeDasharray="3,3" />
        </svg>

        {/* 0 Markers Empty State */}
        {filteredMarkers.length === 0 && (
          <div className="flex flex-col items-center justify-center text-center p-8 space-y-2.5 z-10 max-w-md">
            <div className="w-12 h-12 rounded-2xl bg-slate-800/90 border border-slate-700 flex items-center justify-center text-slate-400 shadow-inner">
              <MapPin className="w-6 h-6 text-slate-500" />
            </div>
            <h4 className="text-sm font-black text-slate-200 tracking-tight">
              No active complaints with verified GPS coordinates.
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed font-medium">
              Civic grievances registered with live GPS telemetry will appear dynamically on this municipal radar matrix.
            </p>
          </div>
        )}

        {/* Real Complaint Hotspot Pins */}
        {filteredMarkers.map((marker) => {
          const isCritical = marker.priority === 'CRITICAL' || (marker.risk_score && marker.risk_score >= 75);
          const isHigh = marker.priority === 'HIGH' || (marker.risk_score && marker.risk_score >= 50);
          const isSelected = selectedPin?.complaint_id === marker.complaint_id;

          // Compute bounded percentage position
          const leftPct = lngRange === 0 
            ? 50 
            : pad + ((Number(marker.longitude) - minLng) / lngRange) * (100 - 2 * pad);
          const topPct = latRange === 0 
            ? 50 
            : (100 - pad) - ((Number(marker.latitude) - minLat) / latRange) * (100 - 2 * pad);

          let pinColor = isCritical 
            ? 'bg-rose-600 text-white ring-rose-500/40' 
            : isHigh 
            ? 'bg-amber-500 text-amber-950 ring-amber-500/40' 
            : 'bg-emerald-600 text-white ring-emerald-500/40';

          return (
            <div
              key={marker.complaint_id}
              style={{ top: `${topPct}%`, left: `${leftPct}%` }}
              className="absolute -translate-x-1/2 -translate-y-1/2 z-10 cursor-pointer group"
              onClick={() => {
                setSelectedPin(marker);
                onSelectComplaint(marker.complaint_id);
              }}
            >
              {isCritical && (
                <span className="absolute -inset-2 rounded-full bg-rose-500/40 animate-ping"></span>
              )}

              <div className={`relative flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold shadow-xl ring-4 transition-all duration-200 group-hover:scale-110 ${pinColor} ${isSelected ? 'scale-125 ring-white' : ''}`}>
                <MapPin className="w-3.5 h-3.5 fill-current" />
                <span className="font-mono text-[11px]">
                  {marker.risk_score !== undefined && marker.risk_score !== null ? marker.risk_score : marker.priority?.[0]}
                </span>
              </div>

              {/* Pin Hover Card */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-60 p-3 rounded-xl bg-slate-900/95 border border-slate-700 shadow-2xl backdrop-blur-md opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-30 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-400 font-mono font-bold">{marker.complaint_id}</span>
                  <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${isCritical ? 'bg-rose-500/20 text-rose-300' : 'bg-amber-500/20 text-amber-300'}`}>
                    {marker.priority || 'NORMAL'}
                  </span>
                </div>
                <div className="text-[11px] font-black text-slate-100 uppercase tracking-wide font-mono">
                  {marker.category || marker.service_type || 'Civic Grievance'}
                </div>
                <p className="text-xs font-medium text-slate-300 line-clamp-2">
                  {marker.complaint_text}
                </p>
                <div className="pt-1 flex items-center justify-between text-[10px] text-slate-400 border-t border-slate-800">
                  <span className="truncate max-w-[120px]">{marker.location_text || marker.jurisdiction || 'GPS Landmark'}</span>
                  {marker.report_count > 1 && (
                    <span className="text-amber-400 font-mono font-bold">+{marker.report_count} reports</span>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {/* Selected Pin Details Overlay Card */}
        {selectedPin && (
          <div className="absolute bottom-4 right-4 z-20 w-80 p-4 rounded-2xl bg-slate-900/95 border border-slate-700 shadow-2xl backdrop-blur-md space-y-2.5 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-mono font-black text-red-400">{selectedPin.complaint_id}</span>
                {selectedPin.report_count > 1 && (
                  <span className="text-[10px] font-mono bg-amber-500/20 text-amber-300 px-1.5 py-0.2 rounded font-bold">
                    {selectedPin.report_count} Reports
                  </span>
                )}
              </div>
              <button 
                onClick={() => setSelectedPin(null)}
                className="text-xs text-slate-400 hover:text-white px-1 font-bold"
              >
                ✕
              </button>
            </div>

            <div>
              <div className="text-xs font-black text-slate-100 uppercase font-mono mb-0.5">
                {selectedPin.category || selectedPin.service_type || 'Civic Issue'}
              </div>
              <p className="text-xs text-slate-300 font-medium line-clamp-2">{selectedPin.complaint_text}</p>
            </div>

            <div className="text-[11px] text-slate-400 flex items-center gap-1">
              <Navigation className="w-3 h-3 text-red-400 shrink-0" />
              <span className="truncate">{selectedPin.location_text || selectedPin.jurisdiction || `GPS (${selectedPin.latitude}, ${selectedPin.longitude})`}</span>
            </div>

            <div className="flex items-center justify-between pt-1 text-xs border-t border-slate-800">
              <div className="flex items-center gap-1.5">
                <PriorityBadge priority={selectedPin.priority} size="sm" />
                <StatusBadge status={selectedPin.status} size="sm" />
              </div>
              {selectedPin.risk_score !== undefined && selectedPin.risk_score !== null && (
                <span className="font-mono text-xs text-red-400 font-bold">Risk: {selectedPin.risk_score}/100</span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Map Footer Bar */}
      <div className="bg-slate-950/90 border-t border-slate-800 px-4 py-2.5 flex flex-wrap items-center justify-between text-[11px] text-slate-400">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-600"></span> Critical Risk (&gt;75)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-500"></span> High Priority (50-74)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-600"></span> Routine Queue (&lt;50)
          </span>
        </div>
        <div className="font-mono text-slate-500">Live Geo-spatial Telemetry Matrix (Real Complaints Only)</div>
      </div>
    </div>
  );
}
