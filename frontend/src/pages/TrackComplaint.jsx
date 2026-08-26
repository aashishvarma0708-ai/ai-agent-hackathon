import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Clock, 
  MapPin, 
  Building2, 
  CheckCircle2, 
  AlertCircle, 
  FileText, 
  UserCheck, 
  Wrench, 
  Calendar, 
  ExternalLink, 
  ShieldAlert,
  Send,
  MessageSquareQuote,
  Sparkles,
  ShieldCheck,
  Check,
  X,
  Users,
  Image as ImageIcon,
  Flame,
  ImageOff
} from 'lucide-react';
import { useComplaints } from '../context/ComplaintContext';
import { getPublicTracking } from '../api/civicresolve';
import PriorityBadge from '../components/PriorityBadge';
import StatusBadge from '../components/StatusBadge';
import RiskGauge from '../components/RiskGauge';
import AgentTraceViewer from '../components/AgentTraceModal';

export default function TrackComplaint({ initialSearchId = '', setActivePage }) {
  const { complaints, getComplaint, updateComplaintStatus, confirmComplaintResolution } = useComplaints();

  const [searchId, setSearchId] = useState(initialSearchId || (complaints[0]?.complaint_id || ''));
  const [complaint, setComplaint] = useState(null);
  const [loading, setLoading] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [followupNote, setFollowupNote] = useState('');
  const [followupSubmitted, setFollowupSubmitted] = useState(false);
  const [citizenFeedbackText, setCitizenFeedbackText] = useState('');
  const [feedbackLoading, setFeedbackLoading] = useState(false);

  const loadTicket = async (idToFind) => {
    if (!idToFind || !idToFind.trim()) return;
    const term = idToFind.trim();
    setLoading(true);
    setNotFound(false);

    try {
      let match = await getComplaint(term);
      if (!match) {
        const publicData = await getPublicTracking(term);
        if (publicData) {
          match = publicData;
        }
      }
      if (match) {
        setComplaint(match);
        setNotFound(false);
      } else {
        setComplaint(null);
        setNotFound(true);
      }
    } catch (e) {
      console.warn("Failed to fetch complaint:", e);
      setNotFound(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialSearchId) {
      setSearchId(initialSearchId);
      loadTicket(initialSearchId);
    } else if (complaints.length > 0 && !complaint) {
      setComplaint(complaints[0]);
    }
  }, [initialSearchId, complaints]);

  const handleSearch = (e) => {
    if (e) e.preventDefault();
    if (!searchId.trim()) return;
    loadTicket(searchId);
  };

  const handleSelectSample = (id) => {
    setSearchId(id);
    loadTicket(id);
  };

  const handleAddCitizenNote = async (e) => {
    e.preventDefault();
    if (!followupNote.trim() || !complaint) return;

    try {
      const updated = await updateComplaintStatus(
        complaint.complaint_id, 
        complaint.status, 
        `Citizen Follow-up: "${followupNote.trim()}"`
      );

      if (updated && typeof updated === 'object') {
        setComplaint(updated);
      } else {
        await loadTicket(complaint.complaint_id);
      }

      setFollowupNote('');
      setFollowupSubmitted(true);
      setTimeout(() => setFollowupSubmitted(false), 3000);
    } catch (err) {
      console.error("Failed to add citizen follow-up:", err);
    }
  };

  const handleCitizenDecision = async (resolved) => {
    if (!complaint) return;
    setFeedbackLoading(true);

    try {
      const updated = await confirmComplaintResolution(
        complaint.complaint_id, 
        resolved, 
        citizenFeedbackText.trim()
      );
      if (updated) {
        setComplaint(updated);
      } else {
        await loadTicket(complaint.complaint_id);
      }
      setCitizenFeedbackText('');
    } catch (err) {
      console.error("Citizen feedback failed:", err);
    } finally {
      setFeedbackLoading(false);
    }
  };

  const steps = [
    { key: 'NEW', label: 'Reported', icon: FileText },
    { key: 'ACKNOWLEDGED', label: 'AI Validated', icon: AlertCircle },
    { key: 'ASSIGNED', label: 'Dept Assigned', icon: UserCheck },
    { key: 'WORK_STARTED', label: 'Work Started', icon: Wrench },
    { key: 'RESOLUTION_SUBMITTED', label: 'Resolution Submitted', icon: ImageIcon },
    { key: 'AI_VERIFICATION_PENDING', label: 'AI Verified', icon: Sparkles },
    { key: 'RESOLVED_PENDING_CITIZEN', label: 'Citizen Confirm', icon: ShieldCheck },
    { key: 'CLOSED', label: 'Closed', icon: CheckCircle2 },
  ];

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
      case 'REOPENED': return 3;
      default: return 0;
    }
  };

  const currentStep = complaint ? getStepIndex(complaint.status) : 0;
  const isPendingCitizen = complaint && (complaint.status === 'RESOLVED_PENDING_CITIZEN' || complaint.status === 'AI_VERIFICATION_PENDING');

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-50 border border-red-200 text-red-700 text-xs font-bold">
          <Search className="w-3.5 h-3.5" />
          <span>Real-Time Audit & Tracking</span>
        </div>
        <h1 className="text-3xl font-black text-[#162044]">
          Track Grievance Resolution & Live Audit
        </h1>
        <p className="text-sm text-slate-600 font-medium">
          Enter any CivicResolve ticket reference to inspect live crew status, SLA countdown, decision audit trails, and dispatch logs.
        </p>
      </div>

      {/* Search Input Bar */}
      <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-md space-y-3">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={searchId}
              onChange={(e) => setSearchId(e.target.value)}
              placeholder="e.g. CR-260820-1042"
              className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs sm:text-sm text-slate-900 font-mono focus:outline-none focus:border-red-500 focus:bg-white transition-all shadow-inner"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2.5 rounded-xl bg-[#e53935] hover:bg-[#d32f2f] text-white font-bold text-xs sm:text-sm transition-colors flex items-center gap-1.5 shadow-md shadow-red-500/20"
          >
            {loading ? <Sparkles className="w-4 h-4 animate-spin text-white" /> : null}
            <span>Track</span>
          </button>
        </form>


      </div>

      {notFound && (
        <div className="p-6 rounded-2xl bg-red-50 border border-red-200 text-red-800 text-center space-y-2">
          <AlertCircle className="w-8 h-8 mx-auto text-red-600" />
          <h3 className="text-base font-black">Complaint ID Not Found</h3>
          <p className="text-xs text-red-700 font-medium">
            Please check the ticket number. Ensure it matches the format `CR-YYMMDD-XXXX`.
          </p>
        </div>
      )}

      {complaint && (
        <div className="space-y-6">
          {/* Main Card */}
          <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-md space-y-8">
            {/* Top Bar with ID, Badges and SLA */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
              <div className="space-y-1">
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold">Tracking Reference</span>
                <div className="flex items-center gap-3">
                  <h2 className="text-2xl font-black text-[#162044] font-mono">{complaint.complaint_id}</h2>
                  <StatusBadge status={complaint.status} size="md" />
                </div>
              </div>

              <div className="flex items-center gap-3 flex-wrap">
                <PriorityBadge priority={complaint.priority} size="md" />

                {complaint.sla_hours > 0 && (
                  <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-mono font-bold ${
                    complaint.sla_info?.is_breached 
                      ? 'bg-red-100 border-red-300 text-red-800 animate-pulse'
                      : complaint.sla_info?.sla_state === 'WARNING'
                      ? 'bg-amber-100 border-amber-300 text-amber-800'
                      : 'bg-blue-50 border-blue-200 text-blue-800'
                  }`}>
                    <Clock className="w-3.5 h-3.5" />
                    <span>
                      {complaint.sla_info?.is_breached ? 'SLA BREACHED' : `SLA: ${complaint.sla_info?.hours_remaining ?? complaint.sla_hours}h left`}
                    </span>
                  </div>
                )}

                {complaint.escalation_level > 0 && (
                  <div className="flex items-center gap-1 px-2.5 py-1 rounded-xl bg-red-100 text-red-800 border border-red-300 text-xs font-mono font-bold">
                    <Flame className="w-3.5 h-3.5 text-red-600" />
                    <span>Tier {complaint.escalation_level} Escalated</span>
                  </div>
                )}
              </div>
            </div>

            {/* 8-Step Lifecycle Progress Stepper */}
            {complaint.domain === 'municipal' && (
              <div className="py-2">
                <div className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-4 font-mono">
                  8-Stage Resolution Lifecycle Stepper
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
                  {steps.map((step, idx) => {
                    const isPassed = idx <= currentStep;
                    const isCurrent = idx === currentStep;
                    const Icon = step.icon;

                    return (
                      <div
                        key={step.key}
                        className={`p-2.5 rounded-2xl border transition-all ${
                          isCurrent
                            ? 'bg-red-50 border-red-300 text-red-700 shadow-sm font-bold scale-105'
                            : isPassed
                            ? 'bg-slate-50 border-slate-300 text-slate-900 font-semibold'
                            : 'bg-slate-50/40 border-slate-200 text-slate-400'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <Icon className={`w-3.5 h-3.5 ${isPassed ? 'text-red-600' : 'text-slate-400'}`} />
                          {isPassed && <CheckCircle2 className="w-3 h-3 text-red-600" />}
                        </div>
                        <p className="text-[10px] font-bold leading-tight truncate">{step.label}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* CITIZEN CONFIRMATION PROMPT (Phase 8) */}
            {isPendingCitizen && (
              <div className="p-6 rounded-2xl bg-emerald-50 border-2 border-emerald-300 space-y-4 shadow-md">
                <div className="flex items-center gap-2.5 text-emerald-900 font-bold text-sm">
                  <ShieldCheck className="w-5 h-5 text-emerald-700" />
                  <span>Citizen Resolution Confirmation Required</span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed font-medium">
                  Municipal work has been reported as completed. Please confirm whether the issue is actually resolved.
                </p>

                <div className="space-y-3">
                  <input
                    type="text"
                    value={citizenFeedbackText}
                    onChange={(e) => setCitizenFeedbackText(e.target.value)}
                    placeholder="Optional feedback note (e.g. 'Road is smooth now' or 'Debris left behind')..."
                    className="w-full px-4 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-emerald-500 shadow-inner"
                  />

                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      disabled={feedbackLoading}
                      onClick={() => handleCitizenDecision(true)}
                      className="flex-1 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-colors shadow-md"
                    >
                      <Check className="w-4 h-4" />
                      <span>Yes, Issue Resolved</span>
                    </button>

                    <button
                      type="button"
                      disabled={feedbackLoading}
                      onClick={() => handleCitizenDecision(false)}
                      className="flex-1 py-2.5 rounded-xl bg-red-100 hover:bg-red-200 text-red-800 border border-red-300 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors"
                    >
                      <X className="w-4 h-4 text-red-600" />
                      <span>No, Issue Still Exists</span>
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* SIDE-BY-SIDE BEFORE / AFTER RESOLUTION EVIDENCE (Phase 7) */}
            {(complaint.initial_image_url || complaint.resolution_image_url || complaint.ai_verification_result) && (
              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-800 font-mono flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-red-600" />
                    <span>Multimodal Resolution Verification Evidence</span>
                  </span>
                  {(() => {
                    const conf = complaint.ai_verification_result?.confidence;
                    if (typeof conf === 'number') {
                      const pct = conf <= 1 ? Math.round(conf * 100) : Math.round(conf);
                      return (
                        <span className="text-[10px] font-mono bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded border border-emerald-200">
                          {pct}% Confidence
                        </span>
                      );
                    }
                    return null;
                  })()}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Before Photo */}
                  <div className="space-y-1.5">
                    <span className="text-[11px] font-bold text-slate-700">1. Initial Citizen Evidence (Before)</span>
                    <div className="rounded-2xl overflow-hidden border border-slate-300 h-44 bg-slate-100 flex items-center justify-center shadow-sm">
                      {complaint.initial_image_url ? (
                        <img 
                          src={complaint.initial_image_url} 
                          alt="Before evidence" 
                          className="w-full h-full object-cover" 
                        />
                      ) : (
                        <div className="flex flex-col items-center justify-center text-center p-4 text-slate-400 space-y-1">
                          <ImageOff className="w-6 h-6 text-slate-400" />
                          <span className="text-[11px] font-medium text-slate-500">No citizen evidence photo was uploaded.</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* After Photo */}
                  <div className="space-y-1.5">
                    <span className="text-[11px] font-bold text-slate-700">2. Field Authority Proof (After Repair)</span>
                    <div className="rounded-2xl overflow-hidden border border-slate-300 h-44 bg-slate-100 flex items-center justify-center shadow-sm">
                      {complaint.resolution_image_url ? (
                        <img 
                          src={complaint.resolution_image_url} 
                          alt="After evidence" 
                          className="w-full h-full object-cover" 
                        />
                      ) : (
                        <div className="flex flex-col items-center justify-center text-center p-4 text-slate-400 space-y-1">
                          <ImageOff className="w-6 h-6 text-slate-400" />
                          <span className="text-[11px] font-medium text-slate-500">No resolution evidence photo has been submitted.</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {complaint.ai_verification_result && (
                  <div className="p-3 rounded-xl bg-white border border-slate-200 text-xs text-slate-800 space-y-1 shadow-sm">
                    <div className="flex items-center gap-1.5 font-bold text-emerald-700">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>
                        AI Verification Result: {complaint.ai_verification_result.appears_resolved ? 'Issue Appears Resolved' : (complaint.ai_verification_result.requires_human_review ? 'Requires Human Review' : 'Resolution Not Verified')}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-600 font-medium">
                      {complaint.ai_verification_result.summary || "Visual comparison recorded by automated resolution pipeline."}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Complaint Key Details Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="md:col-span-2 space-y-4">
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Summary Description</h4>
                  <p className="text-sm text-slate-800 leading-relaxed font-semibold bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                    "{complaint.complaint_text}"
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                    <span className="text-[10px] text-slate-500 font-mono font-bold block">Location / Ward</span>
                    <p className="font-bold text-slate-900 flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-red-600 shrink-0" />
                      <span className="truncate">{complaint.location_text || 'GPS Landmark'}</span>
                    </p>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                    <span className="text-[10px] text-slate-500 font-mono font-bold block">Assigned Authority</span>
                    <p className="font-bold text-slate-900 flex items-center gap-1.5">
                      <Building2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                      <span className="truncate">{complaint.department || complaint.external_service_name || 'Human Verification Desk'}</span>
                    </p>
                  </div>
                </div>

                {complaint.external_service_url && (
                  <div className="p-4 rounded-2xl bg-purple-50 border border-purple-200 space-y-2">
                    <div className="flex items-center gap-2 text-purple-900 font-bold text-xs">
                      <ShieldAlert className="w-4 h-4" />
                      <span>Verified External Service</span>
                    </div>
                    <p className="text-xs text-slate-700 font-medium">
                      {complaint.external_service_name || "Official External Portal"}
                    </p>
                    <a
                      href={complaint.external_service_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-colors"
                    >
                      <span>Open External Service</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                )}
              </div>

              {/* Right Side: Risk Gauge & Meta */}
              <div className="space-y-4">
                {complaint.domain === 'municipal' && (
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
                    <RiskGauge 
                      score={complaint.risk_score} 
                      priority={complaint.priority}
                      reasons={complaint.risk_reasons || []}
                    />
                  </div>
                )}

                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-bold">Intake Channel:</span>
                    <span className="font-mono text-slate-900 font-bold uppercase">{complaint.source_channel}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-bold">Citizen:</span>
                    <span className="font-bold text-slate-900">{complaint.citizen_name || 'Anonymous'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-bold">Citizen Reports:</span>
                    <span className="font-mono font-bold text-red-600">{complaint.report_count || 1} Cumulative</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-bold">Created:</span>
                    <span className="font-mono text-slate-700">{new Date(complaint.created_at || Date.now()).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Linked Supporting Reports (Phase 2) */}
            {complaint.supporting_reports && complaint.supporting_reports.length > 0 && (
              <div className="space-y-3 pt-4 border-t border-slate-200">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 font-mono flex items-center gap-2">
                  <Users className="w-4 h-4 text-amber-600" />
                  <span>Linked Citizen Supporting Reports ({complaint.supporting_reports.length})</span>
                </h4>
                <div className="space-y-2">
                  {complaint.supporting_reports.map((sr, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-amber-50/60 border border-amber-200 text-xs flex justify-between items-center">
                      <div>
                        <span className="font-bold text-slate-900">{sr.citizen_name || 'Citizen'}: </span>
                        <span className="text-slate-700 italic">"{sr.complaint_text}"</span>
                      </div>
                      <span className="text-[10px] font-mono text-amber-800 font-bold shrink-0 ml-2">
                        {Math.round((sr.similarity || 0.85) * 100)}% match
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Status History Audit Log */}
            <div className="space-y-3 pt-4 border-t border-slate-200">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 font-mono flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Official Status Transition Audit Log</span>
              </h4>

              <div className="space-y-2">
                {complaint.history && complaint.history.length > 0 ? (
                  complaint.history.map((h, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                      <div className="flex items-center gap-2.5">
                        <span className="w-2 h-2 rounded-full bg-emerald-600"></span>
                        <StatusBadge status={h.new_status} size="sm" />
                        <span className="text-slate-800 font-medium">{h.note}</span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-500 shrink-0">
                        {new Date(h.changed_at || Date.now()).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-500 italic">No transition logs yet.</p>
                )}
              </div>
            </div>

            {/* Citizen Follow-up Box */}
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
              <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                <MessageSquareQuote className="w-4 h-4 text-red-600" />
                <span>Add Citizen Update or Follow-up Note</span>
              </span>
              <form onSubmit={handleAddCitizenNote} className="flex gap-2">
                <input
                  type="text"
                  value={followupNote}
                  onChange={(e) => setFollowupNote(e.target.value)}
                  placeholder="e.g. Work crew arrived on site at 2 PM, water flow stopped."
                  className="flex-1 px-4 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-red-500 shadow-inner"
                />
                <button
                  type="submit"
                  disabled={!followupNote.trim()}
                  className="px-4 py-2 rounded-xl bg-[#e53935] hover:bg-[#d32f2f] text-white font-bold text-xs flex items-center gap-1 transition-colors disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Send</span>
                </button>
              </form>
              {followupSubmitted && (
                <p className="text-xs text-emerald-700 font-bold">✓ Follow-up note added to audit trail.</p>
              )}
            </div>

            {/* Agent Trace */}
            <AgentTraceViewer trace={complaint.agent_trace} />
          </div>
        </div>
      )}
    </div>
  );
}
