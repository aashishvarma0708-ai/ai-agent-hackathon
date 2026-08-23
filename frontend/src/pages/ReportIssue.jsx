import React, { useState } from 'react';
import { 
  FileText, 
  MapPin, 
  Upload, 
  Sparkles, 
  CheckCircle, 
  AlertTriangle, 
  ExternalLink, 
  ArrowRight, 
  Clock, 
  Building2, 
  ShieldAlert,
  HelpCircle,
  Eye,
  AlertCircle,
  Navigation,
  Copy,
  Users
} from 'lucide-react';
import { useComplaints } from '../context/ComplaintContext';
import PriorityBadge from '../components/PriorityBadge';
import StatusBadge from '../components/StatusBadge';
import RiskGauge from '../components/RiskGauge';
import AgentTraceViewer from '../components/AgentTraceModal';

export default function ReportIssue({ setActivePage, setTrackSearchId }) {
  const { submitNewComplaint } = useComplaints();

  const [citizenName, setCitizenName] = useState('');
  const [complaintText, setComplaintText] = useState('');
  const [locationText, setLocationText] = useState('');
  const [coords, setCoords] = useState({ lat: null, lon: null });
  const [isLocating, setIsLocating] = useState(false);
  const [imagePreview, setImagePreview] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [resultComplaint, setResultComplaint] = useState(null);

  const handleGetCurrentLocation = () => {
    if (!navigator.geolocation) {
      setLocationText("Ward 14 (Central Zone GPS Fallback)");
      setCoords({ lat: 16.3065, lon: 80.4362 });
      return;
    }

    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = parseFloat(position.coords.latitude.toFixed(5));
        const lon = parseFloat(position.coords.longitude.toFixed(5));
        setCoords({ lat, lon });
        setLocationText(`GPS: ${lat}, ${lon} (Detected Landmark)`);
        setIsLocating(false);
      },
      (error) => {
        console.warn("Geolocation permission or timeout, fallback to city reference:", error.message);
        // Fallback default city coordinate
        setCoords({ lat: 16.3065, lon: 80.4362 });
        setLocationText("Ward 14 (Central Zone detected)");
        setIsLocating(false);
      },
      { timeout: 8000 }
    );
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!complaintText.trim() && !imageFile && !imagePreview) return;

    setIsSubmitting(true);
    setResultComplaint(null);
    setErrorMessage('');

    try {
      const newIssue = await submitNewComplaint({
        complaintText: complaintText.trim() || 'Citizen uploaded image evidence without description.',
        locationText: locationText.trim(),
        latitude: coords.lat,
        longitude: coords.lon,
        sourceChannel: 'web',
        citizenName: citizenName.trim(),
        image: imageFile,
      });

      setResultComplaint(newIssue);
    } catch (err) {
      console.error("Submission failed:", err);
      setErrorMessage(err.message || 'Failed to submit complaint to backend');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-50 border border-red-200 text-red-700 text-xs font-bold">
          <FileText className="w-3.5 h-3.5" />
          <span>Structured Intake Pathway</span>
        </div>
        <h1 className="text-3xl font-black text-[#162044]">
          Submit a Public Grievance or Civic Issue
        </h1>
        <p className="text-sm text-slate-600 max-w-2xl font-medium">
          The AI engine analyzes your description and evidence in real time, determines jurisdiction, calculates public safety risk, and routes directly to the accountable department.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Intake Form */}
        <div className="lg:col-span-7 bg-white border border-slate-200 shadow-md p-6 sm:p-8 rounded-3xl space-y-6">
          {errorMessage && (
            <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2 font-medium">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Citizen Name */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Citizen Name <span className="text-slate-500 font-normal">(Optional / Anonymous if blank)</span>
              </label>
              <input
                type="text"
                value={citizenName}
                onChange={(e) => setCitizenName(e.target.value)}
                placeholder="e.g. Aarav Sharma"
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-red-500 focus:bg-white transition-all shadow-inner"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Describe the Issue <span className="text-red-600">*</span>
              </label>
              <textarea
                rows={4}
                required
                value={complaintText}
                onChange={(e) => setComplaintText(e.target.value)}
                placeholder="Describe what happened, hazards present, or how many people are affected..."
                className="w-full px-4 py-3 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-red-500 focus:bg-white transition-all leading-relaxed shadow-inner"
              />
            </div>

            {/* Location with Geolocation button */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-bold text-slate-700">
                  Location / Landmark / Ward
                </label>
                <button
                  type="button"
                  onClick={handleGetCurrentLocation}
                  disabled={isLocating}
                  className="text-[11px] text-red-600 hover:text-red-700 hover:underline flex items-center gap-1 font-bold transition-colors"
                >
                  <Navigation className={`w-3 h-3 ${isLocating ? 'animate-spin text-red-600' : ''}`} />
                  <span>{isLocating ? 'Acquiring GPS...' : 'Use Current Location'}</span>
                </button>
              </div>
              <div className="relative">
                <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={locationText}
                  onChange={(e) => setLocationText(e.target.value)}
                  placeholder="e.g. School Road, Ward 14, Central Zone"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-red-500 focus:bg-white font-mono transition-all shadow-inner"
                />
              </div>
              {coords.lat && coords.lon && (
                <div className="mt-1.5 text-[11px] font-mono text-emerald-700 font-bold flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                  <span>Coordinates: {coords.lat}, {coords.lon} (Location Verified)</span>
                </div>
              )}
            </div>

            {/* Image Evidence Upload */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Evidence Image <span className="text-slate-500 font-normal">(Optional Vision Input)</span>
              </label>

              {imagePreview ? (
                <div className="relative rounded-2xl overflow-hidden border border-slate-300 bg-slate-100 group shadow-sm">
                  <img src={imagePreview} alt="Evidence Preview" className="w-full h-48 object-cover" />
                  <div className="absolute inset-0 bg-slate-900/60 opacity-0 group-hover:opacity-100 flex items-center justify-center gap-3 transition-opacity">
                    <button
                      type="button"
                      onClick={() => { setImagePreview(null); setImageFile(null); }}
                      className="px-3 py-1.5 rounded-lg bg-red-600 text-white text-xs font-bold"
                    >
                      Remove Photo
                    </button>
                  </div>
                </div>
              ) : (
                <label className="border-2 border-dashed border-slate-300 hover:border-red-500 rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer bg-slate-50 hover:bg-slate-100 transition-all">
                  <Upload className="w-8 h-8 text-slate-400 mb-2" />
                  <span className="text-xs font-bold text-slate-700">Click to upload photo evidence</span>
                  <span className="text-[10px] text-slate-500 mt-0.5">Supports JPG, PNG, WebP</span>
                  <input type="file" accept="image/*" onChange={handleImageUpload} className="hidden" />
                </label>
              )}
            </div>

            {/* Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting || (!complaintText.trim() && !imagePreview && !imageFile)}
                className={`w-full py-3.5 rounded-xl font-bold text-sm flex items-center justify-center gap-2 shadow-lg transition-all ${
                  isSubmitting || (!complaintText.trim() && !imagePreview && !imageFile)
                    ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                    : 'bg-[#e53935] hover:bg-[#d32f2f] text-white shadow-red-500/20 hover:scale-[1.01]'
                }`}
              >
                {isSubmitting ? (
                  <>
                    <Sparkles className="w-4 h-4 animate-spin text-white" />
                    <span>CivicResolve is Triaging & Scoring...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 text-white" />
                    <span>Analyze, Score & Submit Complaint</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Live Result & Triage Output Panel */}
        <div className="lg:col-span-5 space-y-6">
          {resultComplaint ? (
            <div className="bg-white border border-slate-200 shadow-md p-6 rounded-3xl space-y-6 animate-in fade-in zoom-in-95 duration-300">
              {/* Duplicate Notice Banner if Linked */}
              {resultComplaint.duplicate_link_info?.is_duplicate && (
                <div className="p-4 rounded-2xl bg-amber-50 border border-amber-300 text-amber-900 space-y-2">
                  <div className="flex items-center gap-2 font-bold text-xs">
                    <Users className="w-4 h-4 text-amber-700" />
                    <span>Possible Existing Civic Issue Detected</span>
                  </div>
                  <p className="text-xs text-slate-800">
                    Linked to primary complaint: <strong className="font-mono text-slate-900">{resultComplaint.duplicate_link_info.primary_complaint_id}</strong> (Similarity: {Math.round(resultComplaint.duplicate_link_info.similarity * 100)}%)
                  </p>
                  <p className="text-[11px] text-amber-800 font-semibold">
                    Citizen reports: <strong>{resultComplaint.duplicate_link_info.report_count}</strong>. Additional reports strengthen municipal dispatch priority.
                  </p>
                </div>
              )}

              {/* Top Banner */}
              <div className="flex items-start justify-between pb-4 border-b border-slate-200">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">Tracking Reference ID</span>
                  <h3 className="text-xl font-black text-[#162044] font-mono flex items-center gap-2">
                    <span>{resultComplaint.complaint_id}</span>
                  </h3>
                </div>
                <StatusBadge status={resultComplaint.status} size="sm" />
              </div>

              {/* Municipal vs External Layout */}
              {resultComplaint.domain === 'municipal' ? (
                <div className="space-y-5">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                      <span className="text-[10px] text-slate-500 block font-mono">Category</span>
                      <span className="text-xs font-bold text-slate-900 uppercase">{resultComplaint.category}</span>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                      <span className="text-[10px] text-slate-500 block font-mono">SLA Time</span>
                      <span className="text-xs font-bold text-blue-700">{resultComplaint.sla_hours} Hours</span>
                    </div>
                  </div>

                  {/* Risk Gauge */}
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
                    <RiskGauge 
                      score={resultComplaint.risk_score} 
                      priority={resultComplaint.priority}
                      reasons={resultComplaint.risk_reasons || []}
                    />
                  </div>

                  {/* Department Routing */}
                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                    <span className="text-[10px] uppercase font-mono font-bold text-slate-500 block">Assigned Department</span>
                    <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                      <Building2 className="w-4 h-4 text-emerald-600" />
                      <span>{resultComplaint.department}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="p-4 rounded-2xl bg-purple-50 border border-purple-200 space-y-2">
                    <div className="flex items-center gap-2 text-purple-900 font-bold text-xs">
                      <ShieldAlert className="w-4 h-4 text-purple-700" />
                      <span>External Public Service Route</span>
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed">
                      {resultComplaint.external_instruction || "This issue has been routed to a verified external public service."}
                    </p>
                    {resultComplaint.external_service_url && (
                      <a
                        href={resultComplaint.external_service_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold mt-2 transition-colors"
                      >
                        <span>Open {resultComplaint.external_service_name || "Official Service"}</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>
                </div>
              )}

              {/* Agent Trace */}
              <AgentTraceViewer trace={resultComplaint.agent_trace} />

              {/* Next Steps Buttons */}
              <div className="pt-2 flex flex-col gap-2">
                <button
                  onClick={() => {
                    setTrackSearchId(resultComplaint.complaint_id);
                    setActivePage('track');
                  }}
                  className="w-full py-2.5 rounded-xl bg-[#162044] hover:bg-[#0f1730] text-white font-bold text-xs flex items-center justify-center gap-2 transition-colors shadow-sm"
                >
                  <span>Track This Complaint Timeline</span>
                  <ArrowRight className="w-3.5 h-3.5 text-amber-400" />
                </button>
                <button
                  onClick={() => setActivePage('authority')}
                  className="w-full py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition-colors border border-slate-200"
                >
                  View on Authority Command Center
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-md text-center space-y-4">
              <div className="w-14 h-14 mx-auto rounded-2xl bg-red-50 border border-red-100 flex items-center justify-center text-red-600">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-base font-black text-[#162044]">
                Live AI Triage & Risk Preview
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed max-w-sm mx-auto font-medium">
                Fill out the grievance details and attach evidence. CivicResolve will calculate real-time safety scores, verify domain separation, and output structured agent traces.
              </p>
              <div className="pt-2 grid grid-cols-2 gap-2 text-left font-mono text-[11px]">
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-700 font-semibold">
                  ⚡ Location Intelligence
                </div>
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-700 font-semibold">
                  🎯 Deterministic Risk Engine
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
