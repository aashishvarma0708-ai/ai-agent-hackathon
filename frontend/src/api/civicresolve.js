const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL;
  if (typeof window !== 'undefined') {
    // If running in Vite dev server (usually :5173 or :3000), default to FastAPI backend on 8000
    if (window.location.port === '5173' || window.location.port === '3000') {
      return 'http://127.0.0.1:8000';
    }
    // In production or unified host mode, use relative root / current origin
    return window.location.origin;
  }
  return 'http://127.0.0.1:8000';
};

const API_BASE_URL = getApiBaseUrl();

/**
 * Health check
 */
export async function checkHealth() {
  const res = await fetch(`${API_BASE_URL}/api/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Authority Command Center Authentication
 */
export async function adminLogin({ email, password }) {
  const res = await fetch(`${API_BASE_URL}/api/admin/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: 'Authentication failed' }));
    throw new Error(errData.detail || 'Invalid administrative credentials');
  }

  return res.json();
}

/**
 * Submit complaint (supports text, location, latitude, longitude, and optional image file/blob)
 */
export async function submitComplaint({
  complaint_text = '',
  location_text = '',
  latitude = null,
  longitude = null,
  citizen_name = '',
  source_channel = 'web',
  language_hint = '',
  image = null,
}) {
  let res;

  if (image) {
    const formData = new FormData();
    formData.append('complaint_text', complaint_text);
    formData.append('location_text', location_text);
    if (latitude !== null && latitude !== undefined) formData.append('latitude', latitude.toString());
    if (longitude !== null && longitude !== undefined) formData.append('longitude', longitude.toString());
    formData.append('citizen_name', citizen_name);
    formData.append('source_channel', source_channel);
    formData.append('language_hint', language_hint);

    if (image instanceof File || image instanceof Blob) {
      formData.append('image', image, 'evidence.jpg');
    }

    res = await fetch(`${API_BASE_URL}/api/complaints`, {
      method: 'POST',
      body: formData,
    });
  } else {
    res = await fetch(`${API_BASE_URL}/api/complaints`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        complaint_text,
        location_text,
        latitude,
        longitude,
        citizen_name,
        source_channel,
        language_hint,
      }),
    });
  }

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || 'Failed to submit complaint');
  }

  return res.json();
}

/**
 * Fetch a single complaint by ID (with history, escalations, supporting reports, live SLA state)
 */
export async function getComplaintById(complaintId) {
  if (!complaintId) return null;
  const cleanId = encodeURIComponent(complaintId.trim().toUpperCase());
  const res = await fetch(`${API_BASE_URL}/api/complaints/${cleanId}`);
  if (!res.ok) {
    if (res.status === 404) return null;
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || `Failed to fetch complaint ${complaintId}`);
  }
  return res.json();
}

/**
 * Fetch all complaints for Authority Dashboard
 */
export async function getAdminComplaints(limit = 200) {
  const res = await fetch(`${API_BASE_URL}/api/admin/complaints?limit=${limit}`);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || 'Failed to fetch admin complaints');
  }
  return res.json();
}

/**
 * Update complaint status
 */
export async function updateStatus(complaintId, status, note = '') {
  const cleanId = encodeURIComponent(complaintId.trim().toUpperCase());
  const res = await fetch(`${API_BASE_URL}/api/complaints/${cleanId}/status`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ status, note }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || `Failed to update status for ${complaintId}`);
  }

  return res.json();
}

/**
 * Citizen Confirmation endpoint (Confirm or contest resolution)
 */
export async function citizenConfirmResolution(complaintId, resolved, comment = '') {
  const cleanId = encodeURIComponent(complaintId.trim().toUpperCase());
  const res = await fetch(`${API_BASE_URL}/api/complaints/${cleanId}/citizen-confirmation`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ resolved, comment }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || `Failed to record citizen confirmation for ${complaintId}`);
  }

  return res.json();
}

/**
 * Trigger batch SLA check and automatic escalation
 */
export async function runSlaCheck() {
  const res = await fetch(`${API_BASE_URL}/api/admin/run-sla-check`, {
    method: 'POST',
  });
  if (!res.ok) {
    throw new Error('Failed to run SLA check');
  }
  return res.json();
}

/**
 * Simulate time advancement for demo SLA breach / escalation testing
 */
export async function simulateComplaintTime(complaintId, hours = 24) {
  const cleanId = encodeURIComponent(complaintId.trim().toUpperCase());
  const res = await fetch(`${API_BASE_URL}/api/admin/complaints/${cleanId}/simulate-time?hours=${hours}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ hours }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || `Failed to simulate time for ${complaintId}`);
  }

  return res.json();
}

/**
 * Dedicated Municipal Work Completion (Mark Work Completed)
 * Submits completion note, resolution proof image, and worker attribution to /api/admin/complaints/{id}/complete-work
 */
export async function completeMunicipalWork(complaintId, { completionNote = '', resolutionImageFile = null, resolutionImageUrl = null, completedBy = '' }) {
  const cleanId = encodeURIComponent(complaintId.trim().toUpperCase());
  const formData = new FormData();
  formData.append('completion_note', completionNote);
  if (completedBy) formData.append('completed_by', completedBy);
  if (resolutionImageUrl) formData.append('resolution_image_url', resolutionImageUrl);
  if (resolutionImageFile instanceof File || resolutionImageFile instanceof Blob) {
    formData.append('resolution_image', resolutionImageFile, 'resolution_proof.jpg');
  }

  const res = await fetch(`${API_BASE_URL}/api/admin/complaints/${cleanId}/complete-work`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || `Failed to complete work for ${complaintId}`);
  }

  return res.json();
}

/**
 * AI Resolution Verification (Before / After evidence comparison)
 */
export async function verifyComplaintResolution(complaintId, notes = '', resolutionImageFile = null, resolutionImageUrl = null) {
  const cleanId = encodeURIComponent(complaintId.trim().toUpperCase());
  const formData = new FormData();
  formData.append('notes', notes);
  if (resolutionImageUrl) formData.append('resolution_image_url', resolutionImageUrl);
  if (resolutionImageFile instanceof File || resolutionImageFile instanceof Blob) {
    formData.append('resolution_image', resolutionImageFile, 'resolution_proof.jpg');
  }

  const res = await fetch(`${API_BASE_URL}/api/admin/complaints/${cleanId}/verify-resolution`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || `Failed to verify resolution for ${complaintId}`);
  }

  return res.json();
}

/**
 * Fetch executive analytics, department performance, and geographic hotspots
 */
export async function getAdminAnalytics() {
  const res = await fetch(`${API_BASE_URL}/api/admin/analytics`);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || 'Failed to fetch analytics');
  }
  return res.json();
}

/**
 * Transcribe voice audio via Whisper STT
 */
export async function transcribeAudio(audioBlobOrFile) {
  const formData = new FormData();
  if (audioBlobOrFile instanceof File || audioBlobOrFile instanceof Blob) {
    const mime = audioBlobOrFile.type || 'audio/webm';
    let ext = 'webm';
    if (mime.includes('wav')) ext = 'wav';
    else if (mime.includes('mp4') || mime.includes('m4a')) ext = 'mp4';
    else if (mime.includes('ogg')) ext = 'ogg';

    const filename = audioBlobOrFile.name || `voice_recording.${ext}`;
    formData.append('audio', audioBlobOrFile, filename);
  } else {
    throw new Error('Invalid audio data provided for transcription');
  }

  const res = await fetch(`${API_BASE_URL}/api/voice/transcribe`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || 'Voice transcription failed');
  }

  return res.json();
}
