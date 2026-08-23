import React, { useState } from 'react';
import { MapPin, Layers } from 'lucide-react';
import PriorityBadge from './PriorityBadge';

export default function HotspotMap({ complaints = [], onSelectComplaint = () => {} }) {
  const [activeCategory, setActiveCategory] = useState('ALL');
  const [selectedPin, setSelectedPin] = useState(null);

  const mockPins = [
    { id: "CR-260820-1042", top: "35%", left: "42%", ward: "Ward 14 (Central)", category: "roads", priority: "CRITICAL", title: "Pothole near St. Mary's School", risk: 88 },
    { id: "CR-260820-8391", top: "58%", left: "68%", ward: "Ward 09 (Green Park)", category: "water", priority: "CRITICAL", title: "Pipeline rupture flooding 4th Cross", risk: 79 },
    { id: "CR-260820-5519", top: "25%", left: "75%", ward: "Sector 4B (East)", category: "garbage", priority: "HIGH", title: "6-day garbage overflow", risk: 54 },
    { id: "CR-260820-2204", top: "65%", left: "28%", ward: "Ward 07 (Nehru Park)", category: "streetlights", priority: "MEDIUM", title: "Dark walkway streetlight outage", risk: 48 },
    { id: "CR-PIN-5", top: "45%", left: "55%", ward: "Ward 12 (Market)", category: "drainage", priority: "HIGH", title: "Stormwater drain blocked by silt", risk: 62 },
    { id: "CR-PIN-6", top: "78%", left: "48%", ward: "Ward 03 (South Ext)", category: "roads", priority: "MEDIUM", title: "Broken pavement & missing manhole cover", risk: 51 },
  ];

  const filteredPins = activeCategory === 'ALL' 
    ? mockPins 
    : mockPins.filter(p => p.category.toLowerCase() === activeCategory.toLowerCase());

  return (
    <div className="relative rounded-2xl overflow-hidden border border-slate-700/80 bg-slate-900 shadow-2xl">
      {/* Map Header / Controls */}
      <div className="absolute top-4 left-4 right-4 z-20 flex flex-wrap items-center justify-between gap-3 pointer-events-auto">
        <div className="flex items-center gap-2 bg-slate-900/90 backdrop-blur-md px-3.5 py-1.5 rounded-xl border border-slate-700 shadow-lg text-xs font-semibold text-slate-200">
          <Layers className="w-4 h-4 text-civic-400" />
          <span>Civic Hotspot GIS Matrix</span>
          <span className="bg-civic-500/20 text-civic-300 px-2 py-0.5 rounded-full text-[10px] font-mono">
            {filteredPins.length} Active Hotspots
          </span>
        </div>

        <div className="flex items-center gap-1.5 bg-slate-900/90 backdrop-blur-md p-1 rounded-xl border border-slate-700 shadow-lg">
          {['ALL', 'roads', 'water', 'garbage', 'drainage', 'streetlights'].map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                activeCategory === cat 
                  ? 'bg-civic-500 text-slate-950 font-bold shadow-md' 
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              {cat === 'ALL' ? 'All Wards' : cat.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Stylized Interactive Map Canvas */}
      <div className="relative w-full h-[400px] bg-slate-950/90 overflow-hidden bg-grid-pattern flex items-center justify-center select-none">
        {/* Radar Scanner Effect */}
        <div className="absolute w-96 h-96 rounded-full border border-civic-500/20 animate-pulse-slow pointer-events-none"></div>
        <div className="absolute w-[580px] h-[580px] rounded-full border border-slate-800/80 pointer-events-none"></div>
        <div className="absolute w-[780px] h-[780px] rounded-full border border-slate-800/40 pointer-events-none"></div>

        {/* Ward Boundaries Decorative Vector Lines */}
        <svg className="absolute inset-0 w-full h-full opacity-30 pointer-events-none">
          <path d="M 50 100 Q 200 150 350 120 T 700 200 T 1100 150" fill="none" stroke="#22c55e" strokeWidth="1.5" strokeDasharray="6,6" />
          <path d="M 120 380 Q 400 300 650 340 T 1000 280" fill="none" stroke="#6366f1" strokeWidth="1" strokeDasharray="4,4" />
          <path d="M 300 20 L 450 220 L 320 380" fill="none" stroke="#0ea5e9" strokeWidth="1" strokeDasharray="3,3" />
        </svg>

        {/* Hotspot Pins */}
        {filteredPins.map((pin) => {
          const isCritical = pin.priority === 'CRITICAL';
          const isHigh = pin.priority === 'HIGH';
          const isSelected = selectedPin?.id === pin.id;

          let pinColor = isCritical 
            ? 'bg-rose-500 text-rose-100 ring-rose-500/40' 
            : isHigh 
            ? 'bg-amber-500 text-amber-100 ring-amber-500/40' 
            : 'bg-civic-500 text-slate-950 ring-civic-500/40';

          return (
            <div
              key={pin.id}
              style={{ top: pin.top, left: pin.left }}
              className="absolute -translate-x-1/2 -translate-y-1/2 z-10 cursor-pointer group"
              onClick={() => {
                setSelectedPin(pin);
                onSelectComplaint(pin.id);
              }}
            >
              {isCritical && (
                <span className="absolute -inset-2 rounded-full bg-rose-500/30 animate-ping"></span>
              )}

              <div className={`relative flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold shadow-xl ring-4 transition-all duration-200 group-hover:scale-110 ${pinColor} ${isSelected ? 'scale-125 ring-white' : ''}`}>
                <MapPin className="w-3.5 h-3.5 fill-current" />
                <span className="font-mono text-[11px]">{pin.risk}</span>
              </div>

              {/* Pin Hover Card */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-52 p-2.5 rounded-xl bg-slate-900/95 border border-slate-700 shadow-2xl backdrop-blur-md opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-30">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-slate-400 font-mono">{pin.ward}</span>
                  <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${isCritical ? 'bg-rose-500/20 text-rose-300' : 'bg-civic-500/20 text-civic-300'}`}>
                    Risk {pin.risk}
                  </span>
                </div>
                <p className="text-xs font-semibold text-slate-100 line-clamp-2">{pin.title}</p>
                <div className="mt-1 text-[10px] text-civic-400 font-mono">ID: {pin.id}</div>
              </div>
            </div>
          );
        })}

        {/* Selected Pin Details Overlay Card */}
        {selectedPin && (
          <div className="absolute bottom-4 right-4 z-20 w-80 p-3.5 rounded-xl bg-slate-900/95 border border-slate-700 shadow-2xl backdrop-blur-md">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
              <span className="text-xs font-bold text-slate-200">{selectedPin.ward}</span>
              <button 
                onClick={() => setSelectedPin(null)}
                className="text-xs text-slate-400 hover:text-white px-1"
              >
                ✕
              </button>
            </div>
            <p className="text-xs text-slate-300 font-medium mb-2">{selectedPin.title}</p>
            <div className="flex items-center justify-between text-xs">
              <PriorityBadge priority={selectedPin.priority} size="sm" />
              <span className="font-mono text-xs text-civic-400 font-bold">Ticket: {selectedPin.id}</span>
            </div>
          </div>
        )}
      </div>

      {/* Map Footer Bar */}
      <div className="bg-slate-950/90 border-t border-slate-800 px-4 py-2.5 flex flex-wrap items-center justify-between text-[11px] text-slate-400">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-500"></span> Critical Risk (&gt;75)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-500"></span> High Priority (50-74)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-civic-500"></span> Routine Queue (&lt;50)
          </span>
        </div>
        <div className="font-mono text-slate-500">Live Geo-spatial Resolution Layer</div>
      </div>
    </div>
  );
}
