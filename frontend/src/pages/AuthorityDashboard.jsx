import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Search, 
  Clock, 
  Building2, 
  ExternalLink, 
  Edit3, 
  Check, 
  Layers,
  ArrowUpRight,
  Flame,
  RefreshCw,
  Sparkles,
  ShieldAlert,
  AlertTriangle,
  Play,
  CheckCircle2,
  MapPin,
  Upload,
  Lock,
  ShieldCheck,
  LogOut,
  KeyRound,
  UserCheck,
  Shield,
  RotateCcw,
  ImageOff,
  Wrench,
  FileText,
  ChevronRight,
  ArrowRight
} from 'lucide-react';
import { useComplaints } from '../context/ComplaintContext';
import { adminLogin } from '../api/civicresolve';
import PriorityBadge from '../components/PriorityBadge';
import StatusBadge from '../components/StatusBadge';
import ComplaintLifecycle from '../components/ComplaintLifecycle';

const ADMIN_ALLOWED_TRANSITIONS = {
  NEW: ['ACKNOWLEDGED', 'ASSIGNED', 'REJECTED', 'EXTERNALLY_ROUTED', 'EMERGENCY_DISPATCHED'],
  ACKNOWLEDGED: ['ASSIGNED', 'WORK_STARTED', 'REJECTED', 'EXTERNALLY_ROUTED', 'EMERGENCY_DISPATCHED'],
  ASSIGNED: ['WORK_STARTED', 'RESOLUTION_SUBMITTED', 'ACKNOWLEDGED', 'REJECTED'],
  WORK_STARTED: ['RESOLUTION_SUBMITTED', 'ASSIGNED', 'REOPENED'],
  RESOLUTION_SUBMITTED: ['AI_VERIFICATION_PENDING', 'RESOLVED_PENDING_CITIZEN', 'HUMAN_REVIEW_REQUIRED', 'REOPENED'],
  AI_VERIFICATION_PENDING: ['RESOLVED_PENDING_CITIZEN', 'HUMAN_REVIEW_REQUIRED', 'REOPENED'],
  HUMAN_REVIEW_REQUIRED: ['RESOLVED_PENDING_CITIZEN', 'REOPENED', 'ASSIGNED', 'WORK_STARTED', 'CLOSED'],
  RESOLVED_PENDING_CITIZEN: ['CLOSED', 'REOPENED'],
  REOPENED: ['ASSIGNED', 'WORK_STARTED', 'RESOLUTION_SUBMITTED'],
  CLOSED: ['REOPENED'],
  REJECTED: ['NEW', 'REOPENED'],
  EXTERNALLY_ROUTED: ['NEW'],
  EMERGENCY_DISPATCHED: ['CLOSED'],
};

const getNextActionInfo = (complaint) => {
  if (!complaint) return null;
  const status = (complaint.status || 'NEW').toUpperCase();

  switch (status) {
    case 'NEW':
      return {
        prompt: 'Acknowledge this complaint.',
        actionLabel: 'Acknowledge',
        actionType: 'ACKNOWLEDGE',
      };
    case 'ACKNOWLEDGED':
      return {
        prompt: 'Assign the complaint to the responsible field team.',
        actionLabel: 'Assign',
        actionType: 'ASSIGN',
      };
    case 'ASSIGNED':
      return {
        prompt: 'Start field work or update field assignment.',
        actionLabel: 'Start Work',
        actionType: 'START_WORK',
      };
    case 'WORK_STARTED':
      return {
        prompt: 'Complete the work and upload resolution evidence.',
        actionLabel: 'Mark Work Completed',
        actionType: 'COMPLETE_WORK',
      };
    case 'RESOLUTION_SUBMITTED':
      return {
        prompt: 'Run AI resolution verification.',
        actionLabel: 'Run AI Verification',
        actionType: 'RUN_AI_VERIFY',
      };
    case 'AI_VERIFICATION_PENDING':
      return {
        prompt: 'AI verification is in progress.',
        actionLabel: 'Inspect Evidence',
        actionType: 'VIEW_EVIDENCE',
      };
    case 'HUMAN_REVIEW_REQUIRED':
      return {
        prompt: 'Review the before/after evidence and approve or reopen the case.',
        actionLabel: 'Review & Decide',
        actionType: 'HUMAN_REVIEW',
      };
    case 'RESOLVED_PENDING_CITIZEN':
      return {
        prompt: 'Waiting for citizen confirmation.',
        actionLabel: 'Inspect Evidence',
        actionType: 'VIEW_EVIDENCE',
      };
    case 'REOPENED':
      return {
        prompt: 'Correct the issue and submit new resolution evidence.',
        actionLabel: 'Mark Work Completed',
        actionType: 'COMPLETE_WORK',
      };
    case 'CLOSED':
      return {
        prompt: 'Complaint lifecycle complete.',
        actionLabel: null,
        actionType: 'NONE',
      };
    default:
      return null;
  }
};

export default function AuthorityDashboard({ setActivePage, setTrackSearchId }) {
  const { 
    complaints, 
    analytics,
    updateComplaintStatus, 
    markWorkCompleted,
    refreshComplaints, 
    verifyResolution,
    loading, 
    backendOnline 
  } = useComplaints();

  // Authentication State for Municipal Command Center
  const AUTH_STORAGE_KEY = 'civicresolve_authority_auth_session';

  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    try {
      const session = sessionStorage.getItem(AUTH_STORAGE_KEY) || localStorage.getItem(AUTH_STORAGE_KEY);
      return !!session;
    } catch {
      return false;
    }
  });

  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [authOfficer, setAuthOfficer] = useState(() => {
    try {
      const session = sessionStorage.getItem(AUTH_STORAGE_KEY) || localStorage.getItem(AUTH_STORAGE_KEY);
      return session ? JSON.parse(session) : null;
    } catch {
      return null;
    }
  });

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!loginEmail.trim() || !loginPassword.trim()) {
      setLoginError('Please enter both official email and password.');
      return;
    }

    setIsAuthenticating(true);
    setLoginError('');

    try {
      const authData = await adminLogin({ email: loginEmail.trim(), password: loginPassword.trim() });

      if (authData && authData.authenticated) {
        const sessionPayload = JSON.stringify(authData.user || { email: loginEmail.trim() });
        sessionStorage.setItem(AUTH_STORAGE_KEY, sessionPayload);
        setIsAuthenticated(true);
        setAuthOfficer(authData.user);
        setLoginEmail('');
        setLoginPassword('');
        refreshComplaints();
      }
    } catch (err) {
      setLoginError(err.message || 'Invalid administrative credentials. Access restricted to authorized personnel.');
    } finally {
      setIsAuthenticating(false);
    }
  };

  const handleLogout = () => {
    try {
      sessionStorage.removeItem(AUTH_STORAGE_KEY);
      localStorage.removeItem(AUTH_STORAGE_KEY);
    } catch {}
    setIsAuthenticated(false);
    setAuthOfficer(null);
  };

  const [filterDomain, setFilterDomain] = useState('ALL');
  const [filterPriority, setFilterPriority] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Routine update modal state
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [updateModalOpen, setUpdateModalOpen] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [statusNote, setStatusNote] = useState('');
  const [updateSuccess, setUpdateSuccess] = useState(false);
  const [updateError, setUpdateError] = useState('');

  // Dedicated Work Completion modal state
  const [completionModalOpen, setCompletionModalOpen] = useState(false);
  const [completionComplaint, setCompletionComplaint] = useState(null);
  const [completionNote, setCompletionNote] = useState('');
  const [completedBy, setCompletedBy] = useState('');
  const [completionImgFile, setCompletionImgFile] = useState(null);
  const [completionImgPreview, setCompletionImgPreview] = useState(null);
  const [completionSubmitting, setCompletionSubmitting] = useState(false);
  const [completionError, setCompletionError] = useState('');
  const [completionSuccess, setCompletionSuccess] = useState(false);

  // Before / After Evidence inspection modal state
  const [evidenceComplaint, setEvidenceComplaint] = useState(null);
  const [evidenceModalOpen, setEvidenceModalOpen] = useState(false);

  // Reopen Case Modal State
  const [reopenModalOpen, setReopenModalOpen] = useState(false);
  const [reopenComplaint, setReopenComplaint] = useState(null);
  const [reopenReason, setReopenReason] = useState('');
  const [reopenSubmitting, setReopenSubmitting] = useState(false);
  const [reopenError, setReopenError] = useState('');

  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    refreshComplaints();
  }, []);

  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    await refreshComplaints();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const municipal = complaints.filter(c => c.domain === 'municipal');
  const openMunicipal = municipal.filter(c => !['CLOSED', 'REJECTED'].includes(c.status));
  const critical = municipal.filter(c => c.priority === 'CRITICAL' && !['CLOSED', 'REJECTED'].includes(c.status));
  const resolved = municipal.filter(c => ['CLOSED', 'RESOLVED_PENDING_CITIZEN'].includes(c.status));

  const filtered = complaints.filter(c => {
    if (filterDomain !== 'ALL' && c.domain !== filterDomain) return false;
    if (filterPriority !== 'ALL' && c.priority !== filterPriority) return false;
    if (filterStatus !== 'ALL' && c.status !== filterStatus) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const match = (c.complaint_id || '').toLowerCase().includes(q) ||
                    (c.complaint_text || '').toLowerCase().includes(q) ||
                    (c.location_text || '').toLowerCase().includes(q) ||
                    (c.category || '').toLowerCase().includes(q) ||
                    (c.department || '').toLowerCase().includes(q);
      if (!match) return false;
    }
    return true;
  });

  const handleOpenUpdate = (complaint) => {
    setSelectedComplaint(complaint);
    const curr = (complaint.status || 'NEW').toUpperCase();
    const allowed = ADMIN_ALLOWED_TRANSITIONS[curr] || [];
    setNewStatus(allowed.length > 0 ? allowed[0] : curr);
    setStatusNote('');
    setUpdateError('');
    setUpdateSuccess(false);
    setUpdateModalOpen(true);
  };

  const handleSaveStatus = async (e) => {
    e.preventDefault();
    if (!selectedComplaint || !newStatus) return;

    try {
      setUpdateError('');
      await updateComplaintStatus(
        selectedComplaint.complaint_id, 
        newStatus, 
        statusNote || `Status transitioned to ${newStatus} from Authority Desk`
      );

      setUpdateSuccess(true);
      await refreshComplaints();
      setTimeout(() => {
        setUpdateSuccess(false);
        setUpdateModalOpen(false);
      }, 600);
    } catch (err) {
      console.error("Failed to update status:", err);
      setUpdateError(err.message || 'Failed to update status.');
    }
  };

  // Dedicated Work Completion Handlers
  const handleOpenCompletion = (complaint) => {
    setCompletionComplaint(complaint);
    setCompletionNote('');
    setCompletedBy('');
    setCompletionImgFile(null);
    setCompletionImgPreview(null);
    setCompletionError('');
    setCompletionSuccess(false);
    setCompletionModalOpen(true);
  };

  const handleCompletionPhotoUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setCompletionImgFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setCompletionImgPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmitCompletion = async (e) => {
    e.preventDefault();
    if (!completionComplaint) return;

    if (!completionNote.trim()) {
      setCompletionError('Completion note is required to verify repairs.');
      return;
    }

    setCompletionError('');
    setCompletionSubmitting(true);

    try {
      await markWorkCompleted(completionComplaint.complaint_id, {
        completionNote: completionNote.trim(),
        resolutionImageFile: completionImgFile,
        resolutionImageUrl: completionImgPreview,
        completedBy: completedBy.trim()
      });

      setCompletionSuccess(true);
      await refreshComplaints();
      setTimeout(() => {
        setCompletionSuccess(false);
        setCompletionModalOpen(false);
      }, 800);
    } catch (err) {
      console.error("Completion submission failed:", err);
      setCompletionError(err.message || 'Failed to submit work completion');
    } finally {
      setCompletionSubmitting(false);
    }
  };

  const handleOpenEvidence = (complaint) => {
    setEvidenceComplaint(complaint);
    setEvidenceModalOpen(true);
  };

  // Reopen Case Handlers
  const handleOpenReopen = (complaint) => {
    setReopenComplaint(complaint);
    setReopenReason('');
    setReopenError('');
    setReopenModalOpen(true);
  };

  const handleConfirmReopen = async (e) => {
    e.preventDefault();
    if (!reopenComplaint) return;

    if (!reopenReason.trim()) {
      setReopenError('A specific reason for reopening is required.');
      return;
    }

    setReopenSubmitting(true);
    setReopenError('');

    try {
      await updateComplaintStatus(
        reopenComplaint.complaint_id,
        'REOPENED',
        `Authority Reopened Case: "${reopenReason.trim()}"`
      );
      setReopenModalOpen(false);
      setEvidenceModalOpen(false);
      await refreshComplaints();
    } catch (err) {
      console.error("Failed to reopen case:", err);
      setReopenError(err.message || 'Failed to reopen case.');
    } finally {
      setReopenSubmitting(false);
    }
  };

  const handleApproveResolution = async (complaint) => {
    if (!complaint) return;
    try {
      await updateComplaintStatus(
        complaint.complaint_id,
        'RESOLVED_PENDING_CITIZEN',
        'Authority manually approved resolution evidence after human review.'
      );
      setEvidenceModalOpen(false);
      await refreshComplaints();
    } catch (err) {
      console.error('Failed to approve resolution:', err);
    }
  };

  const handleExecuteNextAction = async (item, actionType) => {
    if (actionType === 'ACKNOWLEDGE') {
      await updateComplaintStatus(item.complaint_id, 'ACKNOWLEDGED', 'Complaint acknowledged by municipal authority desk.');
      await refreshComplaints();
    } else if (actionType === 'ASSIGN') {
      handleOpenUpdate(item);
    } else if (actionType === 'START_WORK') {
      await updateComplaintStatus(item.complaint_id, 'WORK_STARTED', 'Field crew initiated on-site corrective work.');
      await refreshComplaints();
    } else if (actionType === 'COMPLETE_WORK') {
      handleOpenCompletion(item);
    } else if (actionType === 'RUN_AI_VERIFY') {
      await verifyResolution(item.complaint_id, 'AI verification manually triggered by authority desk.');
      await refreshComplaints();
    } else if (actionType === 'HUMAN_REVIEW' || actionType === 'VIEW_EVIDENCE') {
      handleOpenEvidence(item);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-md mx-auto px-4 py-16 sm:py-24 space-y-6 animate-in fade-in zoom-in-95 duration-200">
        <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-xl space-y-6">
          <div className="text-center space-y-3">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-red-50 border border-red-200 flex items-center justify-center text-red-600 shadow-md shadow-red-500/10">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <div>
              <span className="text-[10px] uppercase font-mono tracking-wider text-red-700 bg-red-50 px-2.5 py-0.5 rounded-full border border-red-200 font-bold">
                Restricted Access
              </span>
              <h2 className="text-2xl font-black text-[#162044] mt-2">Authority Command Center</h2>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed font-medium">
                Single Sign-On authentication for authorized municipal commissioners and dispatch officers.
              </p>
            </div>
          </div>

          {loginError && (
            <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2 font-medium">
              <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
              <span>{loginError}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Official Email Address
              </label>
              <div className="relative">
                <Building2 className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  placeholder="official.email@civicresolve.gov"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-red-500 focus:bg-white transition-all shadow-inner"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Security Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="password"
                  required
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-red-500 focus:bg-white transition-all shadow-inner"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isAuthenticating || !loginEmail.trim() || !loginPassword.trim()}
              className={`w-full py-3 rounded-xl font-bold text-xs sm:text-sm flex items-center justify-center gap-2 shadow-lg transition-all ${
                isAuthenticating || !loginEmail.trim() || !loginPassword.trim()
                  ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                  : 'bg-[#e53935] hover:bg-[#d32f2f] text-white shadow-red-500/20 hover:scale-[1.01]'
              }`}
            >
              {isAuthenticating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  <span>Verifying Credentials...</span>
                </>
              ) : (
                <>
                  <KeyRound className="w-4 h-4 text-white" />
                  <span>Authenticate & Unlock Console</span>
                </>
              )}
            </button>
          </form>

          <div className="pt-2 text-center">
            <button
              type="button"
              onClick={() => setActivePage('home')}
              className="text-xs text-slate-500 hover:text-slate-800 font-semibold transition-colors"
            >
              ← Back to Citizen Portal
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header with Demo Action Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-50 border border-red-200 text-red-700 text-xs font-bold mb-2">
            <LayoutDashboard className="w-3.5 h-3.5" />
            <span>Authority Command Center</span>
            <span className={`w-2 h-2 rounded-full ${backendOnline ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`}></span>
          </div>
          <h1 className="text-3xl font-black text-[#162044]">
            Municipal Operations & Dispatch Desk
          </h1>
          <p className="text-sm text-slate-600 font-medium">
            Real-time command center for municipal dispatch, status updates, and AI resolution verification.
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Refresh Button */}
          <button
            onClick={handleManualRefresh}
            title="Refresh database records"
            className="p-2.5 rounded-xl bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 border border-slate-200 transition-all flex items-center gap-1.5 text-xs font-bold shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-red-600' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          <button
            onClick={() => setActivePage('report')}
            className="px-4 py-2 rounded-xl bg-[#e53935] hover:bg-[#d32f2f] text-white font-bold text-xs shadow-md shadow-red-500/20 transition-all"
          >
            + New Intake
          </button>

          {/* Officer Session Badge & Sign Out Button */}
          <div className="flex items-center gap-2 pl-2 sm:border-l sm:border-slate-200">
            <div className="hidden md:flex flex-col text-right">
              <span className="text-[11px] font-black text-slate-800">{authOfficer?.name || 'Chief Commissioner'}</span>
              <span className="text-[10px] text-slate-500 font-mono">{authOfficer?.email || 'admin@civicresolve.gov'}</span>
            </div>
            <button
              onClick={handleLogout}
              title="Lock Command Center & Sign Out"
              className="px-3 py-2 rounded-xl bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 transition-all flex items-center gap-1.5 text-xs font-bold shadow-sm"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Sign Out</span>
            </button>
          </div>
        </div>
      </div>

      {/* 4 KPI Summary Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-amber-50 border border-amber-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-amber-800">Open Municipal Cases</span>
            <Clock className="w-4 h-4 text-amber-700" />
          </div>
          <div className="mt-2 text-3xl font-black text-amber-950 font-mono">{openMunicipal.length}</div>
          <p className="mt-1 text-[11px] text-amber-800 font-medium">Active in dispatch queue</p>
        </div>

        <div className="p-5 rounded-2xl bg-red-50 border border-red-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-red-800">Critical Priority Alerts</span>
            <Flame className="w-4 h-4 text-red-600" />
          </div>
          <div className="mt-2 text-3xl font-black text-red-950 font-mono">{critical.length}</div>
          <p className="mt-1 text-[11px] text-red-800 font-medium">Immediate risk score &gt;75</p>
        </div>

        <div className="p-5 rounded-2xl bg-sky-50 border border-sky-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-sky-800">Total Registered Cases</span>
            <Building2 className="w-4 h-4 text-sky-700" />
          </div>
          <div className="mt-2 text-3xl font-black text-sky-950 font-mono">{complaints.length}</div>
          <p className="mt-1 text-[11px] text-sky-800 font-medium">Across all jurisdictions</p>
        </div>

        <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-emerald-800">Resolved Grievances</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-700" />
          </div>
          <div className="mt-2 text-3xl font-black text-emerald-950 font-mono">{resolved.length}</div>
          <p className="mt-1 text-[11px] text-emerald-800 font-medium">AI & Citizen verified</p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by ID, keyword, ward..."
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-red-500 focus:bg-white shadow-inner"
          />
        </div>

        {/* Dropdown Filters */}
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          <select
            value={filterDomain}
            onChange={(e) => setFilterDomain(e.target.value)}
            className="px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 font-bold focus:outline-none focus:border-red-500"
          >
            <option value="ALL">All Domains</option>
            <option value="municipal">Municipal Only</option>
            <option value="emergency">Emergency (112)</option>
            <option value="other_public_service">External Services</option>
          </select>

          <select
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value)}
            className="px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 font-bold focus:outline-none focus:border-red-500"
          >
            <option value="ALL">All Priorities</option>
            <option value="CRITICAL">Critical Priority</option>
            <option value="HIGH">High Priority</option>
            <option value="MEDIUM">Medium Priority</option>
            <option value="LOW">Low Priority</option>
            <option value="EXTERNAL">External</option>
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 font-bold focus:outline-none focus:border-red-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="NEW">NEW</option>
            <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
            <option value="ASSIGNED">ASSIGNED</option>
            <option value="WORK_STARTED">WORK STARTED</option>
            <option value="RESOLUTION_SUBMITTED">RESOLUTION SUBMITTED</option>
            <option value="AI_VERIFICATION_PENDING">AI VERIFIED</option>
            <option value="HUMAN_REVIEW_REQUIRED">HUMAN REVIEW REQUIRED</option>
            <option value="RESOLVED_PENDING_CITIZEN">RESOLVED (CITIZEN CONFIRMATION)</option>
            <option value="CLOSED">CLOSED</option>
            <option value="REOPENED">REOPENED</option>
          </select>
        </div>
      </div>

      {/* Main Complaints Data Table */}
      <div className="bg-white rounded-3xl overflow-hidden border border-slate-200 shadow-md">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-[10px] uppercase font-mono tracking-wider text-slate-600 border-b border-slate-200 font-bold">
              <tr>
                <th className="px-5 py-3.5">Ticket ID</th>
                <th className="px-4 py-3.5">Priority / Risk</th>
                <th className="px-4 py-3.5">Category & Summary</th>
                <th className="px-4 py-3.5">Location / Ward</th>
                <th className="px-4 py-3.5">Status & Lifecycle</th>
                <th className="px-4 py-3.5">Next Required Action</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 font-sans">
              {filtered.length > 0 ? (
                filtered.map((item) => {
                  const nextAction = getNextActionInfo(item);

                  return (
                    <tr key={item.complaint_id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-5 py-4 font-mono font-black text-slate-900">
                        <button
                          onClick={() => {
                            setTrackSearchId(item.complaint_id);
                            setActivePage('track');
                          }}
                          className="hover:text-red-600 hover:underline flex items-center gap-1"
                        >
                          <span>{item.complaint_id}</span>
                          <ArrowUpRight className="w-3 h-3 text-slate-400" />
                        </button>
                        <span className="text-[10px] text-slate-500 block font-normal capitalize">
                          via {item.source_channel}
                          {item.report_count > 1 && ` • (${item.report_count} reports)`}
                        </span>
                      </td>

                      <td className="px-4 py-4">
                        <div className="space-y-1">
                          <PriorityBadge priority={item.priority} size="sm" />
                          {item.domain === 'municipal' && (
                            <span className="text-[10px] font-mono text-slate-500 font-semibold block">
                              Risk: <strong className="text-slate-900">{item.risk_score}/100</strong>
                            </span>
                          )}
                        </div>
                      </td>

                      <td className="px-4 py-4 max-w-xs">
                        <div className="font-black text-slate-900 uppercase text-[11px] font-mono">
                          {item.category && item.category !== 'unknown' ? item.category : (item.service_type || 'Civic Issue')}
                        </div>
                        <p className="text-slate-600 truncate text-xs mt-0.5 font-medium" title={item.complaint_text}>
                          {item.complaint_text}
                        </p>
                      </td>

                      <td className="px-4 py-4 text-slate-700">
                        <span className="truncate block max-w-[150px] font-medium" title={item.location_text}>
                          {item.jurisdiction || item.location_text || 'GPS Landmark'}
                        </span>
                      </td>

                      <td className="px-4 py-4">
                        <StatusBadge status={item.status} size="sm" />
                      </td>

                      {/* Next Required Action Column */}
                      <td className="px-4 py-4 max-w-xs">
                        {nextAction ? (
                          <div className="space-y-1">
                            <p className="text-[11px] text-slate-700 font-medium leading-snug">
                              {nextAction.prompt}
                            </p>
                            {nextAction.actionLabel && (
                              <button
                                onClick={() => handleExecuteNextAction(item, nextAction.actionType)}
                                className="px-2.5 py-1 rounded-lg bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 text-[11px] font-bold transition-all inline-flex items-center gap-1 shadow-2xs hover:scale-102 active:scale-98"
                              >
                                <span>{nextAction.actionLabel}</span>
                                <ArrowRight className="w-3 h-3 text-red-600" />
                              </button>
                            )}
                          </div>
                        ) : (
                          <span className="text-[11px] text-slate-400 italic">No action required</span>
                        )}
                      </td>

                      <td className="px-5 py-4 text-right space-x-1.5 whitespace-nowrap">
                        {/* Dedicated Mark Work Completed Button */}
                        {item.domain === 'municipal' && ['ASSIGNED', 'WORK_STARTED', 'REOPENED'].includes(item.status) && (
                          <button
                            onClick={() => handleOpenCompletion(item)}
                            title="Mark work completed and submit resolution proof"
                            className="px-2.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition-all shadow-sm inline-flex items-center gap-1"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span className="hidden xl:inline">Mark Completed</span>
                          </button>
                        )}

                        {/* View Before / After Evidence Button */}
                        {(item.resolution_image_url || item.initial_image_url || item.ai_verification_result || item.status === 'HUMAN_REVIEW_REQUIRED') && (
                          <button
                            onClick={() => handleOpenEvidence(item)}
                            title="Inspect Before / After repair proof and AI verification"
                            className="px-2.5 py-1.5 rounded-lg bg-cyan-50 hover:bg-cyan-100 text-cyan-800 border border-cyan-300 text-xs font-bold transition-all inline-flex items-center gap-1 shadow-xs"
                          >
                            <Sparkles className="w-3 h-3 text-cyan-700" />
                            <span>Evidence</span>
                          </button>
                        )}

                        {/* Routine Update Status Button */}
                        <button
                          onClick={() => handleOpenUpdate(item)}
                          className="px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 hover:text-slate-900 font-bold text-xs transition-colors border border-slate-300 inline-flex items-center gap-1 shadow-xs"
                        >
                          <Edit3 className="w-3 h-3 text-red-600" />
                          <span>Update</span>
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-500 font-medium">
                    No complaints match the selected filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Civic Hotspots Geographic Clusters */}
      {analytics?.hotspots && analytics.hotspots.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-sm font-black uppercase tracking-wider text-slate-800 font-mono flex items-center gap-2">
            <MapPin className="w-4 h-4 text-red-600" />
            <span>Civic Hotspot Risk Clusters (Geographic Matrix)</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {analytics.hotspots.map((hs, idx) => (
              <div key={idx} className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-black text-slate-900">{hs.area}</span>
                  <span className="text-xs font-mono font-black text-red-700 bg-red-50 px-2 py-0.5 rounded border border-red-200">
                    {hs.complaint_count} Active Reports
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-600 font-medium">
                  <span>Top Hazard: <strong className="text-slate-900 uppercase font-mono">{hs.top_category}</strong></span>
                  <span>Cluster Radius: <strong>{hs.radius_m}m</strong></span>
                </div>
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden border border-slate-200">
                  <div 
                    className="bg-red-500 h-full rounded-full" 
                    style={{ width: `${Math.min(100, (hs.complaint_count / (openMunicipal.length || 1)) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Real Department Performance KPIs */}
      {analytics?.department_performance && (
        <div className="space-y-4">
          <h3 className="text-sm font-black uppercase tracking-wider text-slate-800 font-mono flex items-center gap-2">
            <Building2 className="w-4 h-4 text-emerald-600" />
            <span>Department Performance & SLA Compliance Metrics</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(analytics.department_performance).map(([dept, stat]) => (
              <div key={dept} className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-black text-slate-900">{dept}</span>
                  <span className="text-xs font-mono font-black text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    {stat.sla_compliance}% SLA Compliance
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-[11px] font-mono text-slate-600 pt-1 font-semibold">
                  <div>Open: <strong className="text-slate-900">{stat.open}</strong></div>
                  <div>Breached: <strong className="text-red-600">{stat.breached}</strong></div>
                  <div>Avg SLA: <strong className="text-blue-700">{stat.avg_sla_hours}h</strong></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Dedicated Work Completion Modal */}
      {completionModalOpen && completionComplaint && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-3xl p-6 max-w-lg w-full space-y-5 shadow-2xl animate-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-700 font-bold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Municipal Work Completion Submission</span>
                </span>
                <h3 className="text-base font-black text-[#162044] font-mono">{completionComplaint.complaint_id}</h3>
                <p className="text-xs text-slate-600 font-medium">{completionComplaint.category?.toUpperCase()} • {completionComplaint.location_text || 'GPS Landmark'}</p>
              </div>
              <button 
                onClick={() => setCompletionModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 p-1 font-bold"
              >
                ✕
              </button>
            </div>

            {completionError && (
              <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2 font-medium">
                <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
                <span>{completionError}</span>
              </div>
            )}

            <form onSubmit={handleSubmitCompletion} className="space-y-4">
              {/* Completion Note (Required) */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  Completion Note / Work Summary <span className="text-red-600">*</span>
                </label>
                <textarea
                  rows={3}
                  value={completionNote}
                  onChange={(e) => { setCompletionNote(e.target.value); setCompletionError(''); }}
                  placeholder="Describe work completed on-site (e.g. 'Pothole filled with cold mix asphalt, leveled with vibratory compactor, site cleared.')"
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-emerald-500 shadow-inner"
                  required
                />
              </div>

              {/* Resolution Proof Image Upload */}
              <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 space-y-3">
                <span className="text-xs font-bold text-emerald-900 flex items-center gap-1.5">
                  <Upload className="w-3.5 h-3.5 text-emerald-700" />
                  <span>Resolution / After-Work Evidence Image</span>
                </span>

                {completionImgPreview ? (
                  <div className="relative rounded-xl overflow-hidden border border-slate-300 h-40">
                    <img src={completionImgPreview} alt="Resolution Proof Preview" className="w-full h-full object-cover" />
                    <button
                      type="button"
                      onClick={() => { setCompletionImgPreview(null); setCompletionImgFile(null); }}
                      className="absolute top-2 right-2 px-2.5 py-1 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-bold shadow-md"
                    >
                      Remove
                    </button>
                  </div>
                ) : (
                  <label className="border border-dashed border-slate-300 hover:border-emerald-500 rounded-xl p-4 flex flex-col items-center justify-center cursor-pointer bg-white transition-all">
                    <Upload className="w-6 h-6 text-slate-400 mb-1" />
                    <span className="text-xs text-slate-700 font-bold">Click to upload after-repair field image</span>
                    <span className="text-[10px] text-slate-500 mt-0.5">JPG, PNG, or WebP photo from site</span>
                    <input type="file" accept="image/*" onChange={handleCompletionPhotoUpload} className="hidden" />
                  </label>
                )}
              </div>

              {/* Completed By */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  Completed By / Crew Name <span className="text-slate-500">(Optional)</span>
                </label>
                <input
                  type="text"
                  value={completedBy}
                  onChange={(e) => setCompletedBy(e.target.value)}
                  placeholder="e.g. Rapid Road Repair Unit #4 / Officer Ramesh"
                  className="w-full px-4 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-emerald-500 shadow-inner"
                />
              </div>

              {/* Workflow Status Info */}
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-600 space-y-1">
                <div className="font-bold text-slate-800 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-red-600" />
                  <span>Automated Verification Pipeline</span>
                </div>
                <p>
                  Submitting transitions status to <strong className="text-emerald-700 font-mono">RESOLUTION_SUBMITTED</strong> and triggers Multimodal AI Verification. Ticket will NOT be marked CLOSED directly.
                </p>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setCompletionModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={completionSubmitting}
                  className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-md disabled:opacity-50"
                >
                  {completionSubmitting ? (
                    <>
                      <Sparkles className="w-4 h-4 animate-spin text-white" />
                      <span>Verifying Resolution...</span>
                    </>
                  ) : completionSuccess ? (
                    <>
                      <Check className="w-4 h-4 text-white" />
                      <span>Completed & AI Verified!</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4 text-white" />
                      <span>Submit Completion</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Before / After Evidence Viewer & Lifecycle Modal */}
      {evidenceModalOpen && evidenceComplaint && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-3xl p-6 max-w-3xl w-full space-y-5 shadow-2xl animate-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-700 font-bold flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-cyan-600" />
                  <span>Multimodal Evidence Audit & Lifecycle Review</span>
                </span>
                <h3 className="text-base font-black text-[#162044] font-mono">{evidenceComplaint.complaint_id}</h3>
              </div>
              <button 
                onClick={() => setEvidenceModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 p-1 font-bold"
              >
                ✕
              </button>
            </div>

            {/* Lifecycle Progress Visualizer */}
            <div className="space-y-2">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">Lifecycle Progress</span>
              <ComplaintLifecycle currentStatus={evidenceComplaint.status} />
            </div>

            {/* Side by side comparison (REAL IMAGES ONLY, NO STOCK/UNSPLASH FALLBACKS) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <span className="text-xs font-bold text-slate-700">1. Citizen Initial Evidence (Before)</span>
                <div className="rounded-2xl overflow-hidden border border-slate-300 h-48 bg-slate-100 flex items-center justify-center shadow-inner">
                  {evidenceComplaint.initial_image_url ? (
                    <img 
                      src={evidenceComplaint.initial_image_url} 
                      alt="Citizen initial evidence" 
                      className="w-full h-full object-cover" 
                    />
                  ) : (
                    <div className="flex flex-col items-center justify-center text-center p-4 text-slate-400 space-y-1">
                      <ImageOff className="w-8 h-8 text-slate-400" />
                      <span className="text-xs font-medium text-slate-500">No citizen evidence photo was uploaded.</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="space-y-1.5">
                <span className="text-xs font-bold text-slate-700">2. Field Authority Proof (After Repair)</span>
                <div className="rounded-2xl overflow-hidden border border-slate-300 h-48 bg-slate-100 flex items-center justify-center shadow-inner">
                  {evidenceComplaint.resolution_image_url ? (
                    <img 
                      src={evidenceComplaint.resolution_image_url} 
                      alt="Field resolution proof" 
                      className="w-full h-full object-cover" 
                    />
                  ) : (
                    <div className="flex flex-col items-center justify-center text-center p-4 text-slate-400 space-y-1">
                      <ImageOff className="w-8 h-8 text-slate-400" />
                      <span className="text-xs font-medium text-slate-500">No resolution evidence photo has been submitted.</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* AI Verification Result Panel */}
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5 font-mono uppercase">
                  <Sparkles className="w-4 h-4 text-red-600" />
                  <span>AI RESOLUTION VERIFICATION</span>
                </span>
                <span className="text-xs font-mono font-bold text-slate-800 bg-white px-2 py-0.5 rounded border border-slate-200">
                  {(() => {
                    const conf = evidenceComplaint?.ai_verification_result?.confidence;
                    if (typeof conf === 'number') {
                      const pct = conf <= 1 ? Math.round(conf * 100) : Math.round(conf);
                      return `${pct}% Confidence`;
                    }
                    return 'Confidence unavailable';
                  })()}
                </span>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <span className="text-xs text-slate-600 font-bold">Result:</span>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold font-mono ${
                  evidenceComplaint.ai_verification_result?.appears_resolved
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                    : evidenceComplaint.ai_verification_result?.requires_human_review || evidenceComplaint.status === 'HUMAN_REVIEW_REQUIRED'
                    ? 'bg-amber-100 text-amber-800 border border-amber-300'
                    : 'bg-red-100 text-red-800 border border-red-300'
                }`}>
                  {evidenceComplaint.ai_verification_result?.appears_resolved
                    ? 'Appears Resolved'
                    : evidenceComplaint.ai_verification_result?.requires_human_review || evidenceComplaint.status === 'HUMAN_REVIEW_REQUIRED'
                    ? 'Requires Human Review'
                    : 'Resolution Not Verified'}
                </span>
              </div>

              <p className="text-xs text-slate-700 font-medium pt-1 leading-relaxed">
                {evidenceComplaint.ai_verification_result?.summary || evidenceComplaint.resolution_summary || "Visual comparison recorded by automated resolution pipeline."}
              </p>
            </div>

            {/* Next Required Action Banner & Authority Decision Buttons */}
            {evidenceComplaint.status === 'HUMAN_REVIEW_REQUIRED' && (
              <div className="p-4 rounded-2xl bg-amber-50 border border-amber-300 space-y-3">
                <div className="flex items-center gap-2 text-amber-900 font-bold text-xs">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                  <span>NEXT REQUIRED ACTION: Review before/after evidence and approve or reopen the case.</span>
                </div>
                <div className="flex flex-wrap items-center justify-end gap-2.5 pt-1">
                  <button
                    onClick={() => handleOpenReopen(evidenceComplaint)}
                    className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Reopen Case</span>
                  </button>
                  <button
                    onClick={() => handleApproveResolution(evidenceComplaint)}
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Approve Resolution</span>
                  </button>
                </div>
              </div>
            )}

            {evidenceComplaint.status === 'RESOLVED_PENDING_CITIZEN' && (
              <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs font-medium flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-700 shrink-0" />
                <span>Resolution verified. Waiting for citizen confirmation.</span>
              </div>
            )}

            {evidenceComplaint.status === 'REOPENED' && (
              <div className="p-3.5 rounded-2xl bg-red-50 border border-red-200 text-red-900 text-xs font-medium flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <RotateCcw className="w-4 h-4 text-red-600 shrink-0" />
                  <span>Case Reopened — corrective field work required before re-submission.</span>
                </div>
                <button
                  onClick={() => {
                    setEvidenceModalOpen(false);
                    handleOpenCompletion(evidenceComplaint);
                  }}
                  className="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-bold"
                >
                  Submit New Resolution
                </button>
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setEvidenceModalOpen(false)}
                className="px-5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Routine Update Status Modal (Constrained to Allowed Transitions) */}
      {updateModalOpen && selectedComplaint && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-3xl p-6 max-w-lg w-full space-y-5 shadow-2xl animate-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold">Update Authority Status</span>
                <h3 className="text-base font-black text-[#162044] font-mono">{selectedComplaint.complaint_id}</h3>
                <span className="text-xs text-slate-600 font-mono">Current Status: <strong>{selectedComplaint.status}</strong></span>
              </div>
              <button 
                onClick={() => setUpdateModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 p-1 font-bold"
              >
                ✕
              </button>
            </div>

            {updateError && (
              <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2 font-medium">
                <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
                <span>{updateError}</span>
              </div>
            )}

            <form onSubmit={handleSaveStatus} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  Allowed Status Transitions (From {selectedComplaint.status})
                </label>
                {(() => {
                  const curr = (selectedComplaint.status || 'NEW').toUpperCase();
                  const allowed = ADMIN_ALLOWED_TRANSITIONS[curr] || [];

                  if (allowed.length === 0) {
                    return (
                      <p className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 italic">
                        No direct administrative status transitions available from status '{curr}'. Please use the dedicated resolution workflow.
                      </p>
                    );
                  }

                  return (
                    <select
                      value={newStatus}
                      onChange={(e) => setNewStatus(e.target.value)}
                      className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs sm:text-sm text-slate-900 font-mono focus:outline-none focus:border-red-500 shadow-inner"
                    >
                      {allowed.map((st) => (
                        <option key={st} value={st}>
                          {st}
                        </option>
                      ))}
                    </select>
                  );
                })()}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  Officer Action Notes / Transition Log
                </label>
                <textarea
                  rows={3}
                  value={statusNote}
                  onChange={(e) => setStatusNote(e.target.value)}
                  placeholder="e.g. Dispatched Road Repair Unit #4 to site for initial assessment."
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-red-500 shadow-inner"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setUpdateModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!newStatus || (ADMIN_ALLOWED_TRANSITIONS[(selectedComplaint.status || 'NEW').toUpperCase()] || []).length === 0}
                  className="px-5 py-2 rounded-xl bg-[#e53935] hover:bg-[#d32f2f] text-white text-xs font-bold transition-colors flex items-center gap-1.5 shadow-md shadow-red-500/20 disabled:opacity-50"
                >
                  {updateSuccess ? (
                    <>
                      <Check className="w-4 h-4 text-white" />
                      <span>Updated!</span>
                    </>
                  ) : (
                    <span>Save Transition</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reopen Case Reason Modal */}
      {reopenModalOpen && reopenComplaint && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-3xl p-6 max-w-md w-full space-y-5 shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-red-700 font-bold flex items-center gap-1">
                  <RotateCcw className="w-3.5 h-3.5 text-red-600" />
                  <span>Reopen Case for Rework</span>
                </span>
                <h3 className="text-base font-black text-[#162044] font-mono">{reopenComplaint.complaint_id}</h3>
              </div>
              <button 
                onClick={() => setReopenModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 p-1 font-bold"
              >
                ✕
              </button>
            </div>

            {reopenError && (
              <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2 font-medium">
                <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
                <span>{reopenError}</span>
              </div>
            )}

            <form onSubmit={handleConfirmReopen} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  Reason for Reopening <span className="text-red-600">*</span>
                </label>
                <textarea
                  rows={3}
                  required
                  value={reopenReason}
                  onChange={(e) => { setReopenReason(e.target.value); setReopenError(''); }}
                  placeholder="e.g. Uploaded repair photo does not show the reported pothole repaired."
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-red-500 shadow-inner"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setReopenModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={reopenSubmitting || !reopenReason.trim()}
                  className="px-5 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-md shadow-red-500/20 disabled:opacity-50"
                >
                  {reopenSubmitting ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin text-white" />
                      <span>Reopening Case...</span>
                    </>
                  ) : (
                    <>
                      <RotateCcw className="w-4 h-4 text-white" />
                      <span>Confirm & Reopen</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
