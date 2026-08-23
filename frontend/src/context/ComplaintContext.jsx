import React, { createContext, useContext, useState, useEffect } from 'react';
import { INITIAL_COMPLAINTS } from '../data/mockComplaints';
import { 
  getAdminComplaints, 
  submitComplaint, 
  getComplaintById, 
  updateStatus as apiUpdateStatus,
  citizenConfirmResolution,
  simulateComplaintTime,
  completeMunicipalWork,
  verifyComplaintResolution,
  getAdminAnalytics,
  runSlaCheck
} from '../api/civicresolve';

const ComplaintContext = createContext(null);

const STORAGE_KEY = 'civicresolve_complaints_v1';

export function ComplaintProvider({ children }) {
  const [complaints, setComplaints] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (e) {
      console.warn("Failed to load complaints from storage:", e);
    }
    return INITIAL_COMPLAINTS;
  });

  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);

  // Sync complaints & analytics with real backend on mount
  const refreshComplaints = async () => {
    try {
      setLoading(true);
      const data = await getAdminComplaints();
      if (Array.isArray(data) && data.length > 0) {
        setComplaints(data);
        setBackendOnline(true);
      }
      // Also fetch analytics
      const anData = await getAdminAnalytics();
      if (anData) {
        setAnalytics(anData);
      }
    } catch (e) {
      console.warn("Backend API not reachable yet, using client cache/mock data:", e.message);
      setBackendOnline(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshComplaints();
  }, []);

  // Save to local storage for offline resiliency
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(complaints));
    } catch (e) {
      console.error("Failed to save complaints to storage:", e);
    }
  }, [complaints]);

  // Reset to initial demo dataset
  const resetToDemo = () => {
    setComplaints(INITIAL_COMPLAINTS);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_COMPLAINTS));
    } catch (e) {}
  };

  // Submit new complaint to real backend
  const submitNewComplaint = async ({
    complaintText = '',
    locationText = '',
    latitude = null,
    longitude = null,
    citizenName = '',
    sourceChannel = 'web',
    languageHint = '',
    image = null,
  }) => {
    try {
      setLoading(true);
      const newComplaint = await submitComplaint({
        complaint_text: complaintText,
        location_text: locationText,
        latitude: latitude,
        longitude: longitude,
        citizen_name: citizenName,
        source_channel: sourceChannel,
        language_hint: languageHint,
        image: image,
      });

      // Ensure agent_trace is parsed
      if (typeof newComplaint.agent_trace === 'string') {
        try {
          newComplaint.agent_trace = JSON.parse(newComplaint.agent_trace);
        } catch (e) {
          newComplaint.agent_trace = [];
        }
      }

      setComplaints(prev => {
        // If linked as supporting report to existing complaint, replace in list
        const existingIdx = prev.findIndex(c => c.complaint_id === newComplaint.complaint_id);
        if (existingIdx >= 0) {
          const copy = [...prev];
          copy[existingIdx] = newComplaint;
          return copy;
        }
        return [newComplaint, ...prev];
      });

      setBackendOnline(true);
      return newComplaint;
    } catch (err) {
      console.error("submitNewComplaint error:", err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Update complaint status in real backend
  const updateComplaintStatus = async (complaintId, newStatus, note = '') => {
    try {
      setLoading(true);
      const updated = await apiUpdateStatus(complaintId, newStatus, note);
      
      setComplaints(prev => prev.map(item => 
        item.complaint_id === complaintId ? (updated || { ...item, status: newStatus }) : item
      ));
      return updated || true;
    } catch (err) {
      console.warn("Backend update failed, updating local state:", err.message);
      setComplaints(prev => prev.map(item => {
        if (item.complaint_id === complaintId) {
          const now = new Date().toISOString();
          return {
            ...item,
            status: newStatus,
            updated_at: now,
            history: [
              ...(item.history || []),
              {
                old_status: item.status,
                new_status: newStatus,
                note: note || `Status transitioned to ${newStatus}`,
                changed_at: now
              }
            ]
          };
        }
        return item;
      }));
      return true;
    } finally {
      setLoading(false);
    }
  };

  // Citizen confirms or contests resolution
  const confirmComplaintResolution = async (complaintId, resolved, comment = '') => {
    try {
      setLoading(true);
      const updated = await citizenConfirmResolution(complaintId, resolved, comment);
      setComplaints(prev => prev.map(item => 
        item.complaint_id === complaintId ? (updated || item) : item
      ));
      return updated;
    } finally {
      setLoading(false);
    }
  };

  // Simulate time advancement (Demo mode)
  const simulateTime = async (complaintId, hours = 24) => {
    try {
      setLoading(true);
      const updated = await simulateComplaintTime(complaintId, hours);
      setComplaints(prev => prev.map(item => 
        item.complaint_id === complaintId ? (updated || item) : item
      ));
      return updated;
    } finally {
      setLoading(false);
    }
  };

  // Verify resolution evidence (Before/After AI verification)
  const verifyResolution = async (complaintId, notes = '', resolutionImageFile = null, resolutionImageUrl = null) => {
    try {
      setLoading(true);
      const updated = await verifyComplaintResolution(complaintId, notes, resolutionImageFile, resolutionImageUrl);
      setComplaints(prev => prev.map(item => 
        item.complaint_id === complaintId ? (updated || item) : item
      ));
      return updated;
    } finally {
      setLoading(false);
    }
  };

  // Dedicated Municipal Work Completion Workflow
  const markWorkCompleted = async (complaintId, { completionNote = '', resolutionImageFile = null, resolutionImageUrl = null, completedBy = '' }) => {
    try {
      setLoading(true);
      const updated = await completeMunicipalWork(complaintId, {
        completionNote,
        resolutionImageFile,
        resolutionImageUrl,
        completedBy,
      });
      setComplaints(prev => prev.map(item => 
        item.complaint_id === complaintId ? (updated || item) : item
      ));
      return updated;
    } finally {
      setLoading(false);
    }
  };

  // Trigger batch SLA check
  const triggerSlaCheck = async () => {
    try {
      setLoading(true);
      const result = await runSlaCheck();
      await refreshComplaints();
      return result;
    } finally {
      setLoading(false);
    }
  };

  // Fetch single complaint by ID from real backend
  const getComplaint = async (id) => {
    if (!id) return null;
    const cleanId = id.trim().toUpperCase();

    try {
      const fromBackend = await getComplaintById(cleanId);
      if (fromBackend) return fromBackend;
    } catch (e) {
      console.warn("Backend fetch failed, checking local list:", e.message);
    }

    return complaints.find(c => c.complaint_id.toUpperCase() === cleanId) || null;
  };

  return (
    <ComplaintContext.Provider value={{
      complaints,
      analytics,
      loading,
      backendOnline,
      submitNewComplaint,
      updateComplaintStatus,
      confirmComplaintResolution,
      simulateTime,
      markWorkCompleted,
      verifyResolution,
      triggerSlaCheck,
      getComplaint,
      refreshComplaints,
      resetToDemo,
    }}>
      {children}
    </ComplaintContext.Provider>
  );
}

export function useComplaints() {
  const context = useContext(ComplaintContext);
  if (!context) {
    throw new Error('useComplaints must be used within a ComplaintProvider');
  }
  return context;
}
