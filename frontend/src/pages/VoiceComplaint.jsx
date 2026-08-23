import React, { useState, useEffect, useRef } from 'react';
import { 
  Mic, 
  Square, 
  Sparkles, 
  Globe, 
  MapPin, 
  ArrowRight, 
  Building2,
  Radio,
  AlertCircle,
  Navigation,
  Edit3,
  Loader2,
  Users
} from 'lucide-react';
import { useComplaints } from '../context/ComplaintContext';
import { transcribeAudio } from '../api/civicresolve';
import PriorityBadge from '../components/PriorityBadge';
import StatusBadge from '../components/StatusBadge';
import RiskGauge from '../components/RiskGauge';
import AgentTraceViewer from '../components/AgentTraceModal';

export default function VoiceComplaint({ setActivePage, setTrackSearchId }) {
  const { submitNewComplaint } = useComplaints();

  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [recordDuration, setRecordDuration] = useState(0);
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [detectedLanguage, setDetectedLanguage] = useState('');
  const [hasRecorded, setHasRecorded] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [locationText, setLocationText] = useState('');
  const [coords, setCoords] = useState({ lat: null, lon: null });
  const [isLocating, setIsLocating] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [resultComplaint, setResultComplaint] = useState(null);
  const [audioBlob, setAudioBlob] = useState(null);

  const timerRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const languages = [
    { code: 'en', label: 'English' },
    { code: 'te', label: 'Telugu (తెలుగు)' },
    { code: 'hi', label: 'Hindi (हिन्दी)' },
    { code: 'ta', label: 'Tamil (தமிழ்)' },
    { code: 'kn', label: 'Kannada (ಕನ್ನಡ)' },
  ];

  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setRecordDuration(prev => prev + 1);
      }, 1000);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [isRecording]);

  const handleTranscribeAudio = async (blob) => {
    setIsTranscribing(true);
    setErrorMessage('');
    setTranscript('');

    try {
      const result = await transcribeAudio(blob);
      console.log("TRANSCRIPTION RESPONSE:", result);

      if (result && result.text && result.text.trim()) {
        setTranscript(result.text.trim());
        setDetectedLanguage(result.language || "Unknown");
        setHasRecorded(true);
      } else {
        setErrorMessage("Voice transcription failed. Please try recording again.");
        setTranscript('');
        setHasRecorded(false);
      }
    } catch (err) {
      console.error("Transcription error:", err);
      setErrorMessage("Voice transcription failed. Please try recording again.");
      setTranscript('');
      setHasRecorded(false);
    } finally {
      setIsTranscribing(false);
    }
  };

  const handleStartRecord = async () => {
    setErrorMessage('');
    setIsRecording(true);
    setRecordDuration(0);
    setHasRecorded(false);
    setTranscript('');
    setDetectedLanguage('');
    setResultComplaint(null);
    setAudioBlob(null);

    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunksRef.current = [];

        let mimeType = 'audio/webm';
        if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
          mimeType = 'audio/webm;codecs=opus';
        } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
          mimeType = 'audio/mp4';
        }

        const mediaRecorder = new MediaRecorder(stream, { mimeType });
        mediaRecorderRef.current = mediaRecorder;

        mediaRecorder.ondataavailable = (event) => {
          if (event.data && event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.onstop = () => {
          const blob = new Blob(audioChunksRef.current, { type: mediaRecorder.mimeType || 'audio/webm' });
          setAudioBlob(blob);
          stream.getTracks().forEach(track => track.stop());

          // Immediately transcribe recorded audio through Whisper API
          handleTranscribeAudio(blob);
        };

        mediaRecorder.start(250);
      } else {
        setErrorMessage("Microphone access is not supported by your browser.");
        setIsRecording(false);
      }
    } catch (e) {
      console.error("Microphone hardware access error:", e);
      setErrorMessage("Microphone access was denied or unavailable. Please enable microphone permissions.");
      setIsRecording(false);
    }
  };

  const handleStopRecord = () => {
    setIsRecording(false);

    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {
        console.warn("Error stopping media recorder:", e);
      }
    }
  };

  const handleGetCurrentLocation = () => {
    if (!navigator.geolocation) {
      setLocationText("Ward 14 (Central Zone GPS)");
      setCoords({ lat: 16.3065, lon: 80.4362 });
      return;
    }

    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = parseFloat(position.coords.latitude.toFixed(5));
        const lon = parseFloat(position.coords.longitude.toFixed(5));
        setCoords({ lat, lon });
        setLocationText(`GPS: ${lat}, ${lon} (Voice Detected Location)`);
        setIsLocating(false);
      },
      () => {
        setCoords({ lat: 16.3065, lon: 80.4362 });
        setLocationText("Ward 14 (Central Zone GPS)");
        setIsLocating(false);
      },
      { timeout: 8000 }
    );
  };

  const handleProcessVoice = async () => {
    console.log("SUBMITTING VOICE TRANSCRIPT:", transcript);
    if (!transcript || !transcript.trim()) return;

    setIsProcessing(true);
    setErrorMessage('');

    try {
      const res = await submitNewComplaint({
        complaintText: transcript.trim(),
        locationText: locationText || 'Location provided via Voice Intake GPS',
        latitude: coords.lat,
        longitude: coords.lon,
        sourceChannel: 'voice',
        citizenName: 'Voice Citizen',
        languageHint: detectedLanguage || selectedLanguage,
      });

      setResultComplaint(res);
    } catch (err) {
      console.error("Voice processing error:", err);
      setErrorMessage(err.message || 'Failed to process voice complaint');
    } finally {
      setIsProcessing(false);
    }
  };

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400 text-xs font-semibold">
          <Radio className="w-3.5 h-3.5 animate-pulse" />
          <span>Multilingual Voice Intake Studio</span>
        </div>
        <h1 className="text-3xl font-extrabold text-white">
          Speak Your Complaint Naturally
        </h1>
        <p className="text-sm text-slate-400 max-w-2xl">
          Zero typing required. Speak in Telugu, Hindi, Tamil, Kannada, or English. Groq Whisper STT auto-transcribes, translates, and passes the grievance to the exact same CivicResolve pipeline.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Studio Recording Console */}
        <div className="lg:col-span-7 glass-panel p-6 sm:p-8 rounded-3xl space-y-6 border border-slate-800">
          {errorMessage && (
            <div className="p-4 rounded-2xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Language Selector */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5 text-sky-400" />
              <span>Select Spoken Language / Dialect</span>
            </label>
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-xs sm:text-sm text-white font-medium focus:outline-none focus:border-sky-500"
            >
              {languages.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>

          {/* Microphone Recording Center */}
          <div className="p-8 rounded-2xl bg-slate-950/80 border border-slate-800/90 flex flex-col items-center justify-center space-y-6 text-center">
            {/* Audio Waveform Simulator */}
            <div className="h-12 flex items-center gap-1.5 px-4">
              {[...Array(18)].map((_, i) => (
                <div
                  key={i}
                  className={`w-1.5 rounded-full transition-all ${
                    isRecording 
                      ? 'bg-sky-400 audio-bar' 
                      : isTranscribing
                      ? 'bg-amber-400 animate-pulse h-5'
                      : hasRecorded 
                      ? 'bg-emerald-500/60 h-6' 
                      : 'bg-slate-800 h-2'
                  }`}
                  style={isRecording ? { animationDelay: `${(i * 0.08).toFixed(2)}s`, animationDuration: '0.9s' } : {}}
                />
              ))}
            </div>

            {/* Timer Display */}
            <div className="font-mono text-2xl font-black text-white">
              {formatTime(recordDuration)}
            </div>

            {/* Big Mic Button */}
            <div className="relative">
              {isRecording && (
                <span className="absolute -inset-3 rounded-full bg-rose-500/20 animate-ping"></span>
              )}
              <button
                type="button"
                disabled={isTranscribing}
                onClick={isRecording ? handleStopRecord : handleStartRecord}
                className={`relative w-20 h-20 rounded-full flex items-center justify-center shadow-2xl transition-all hover:scale-105 active:scale-95 ${
                  isRecording
                    ? 'bg-rose-500 text-white shadow-rose-500/30'
                    : isTranscribing
                    ? 'bg-slate-800 text-slate-400 cursor-not-allowed'
                    : 'bg-gradient-to-tr from-sky-600 to-cyan-400 text-slate-950 shadow-sky-500/30'
                }`}
              >
                {isRecording ? (
                  <Square className="w-8 h-8 fill-current" />
                ) : isTranscribing ? (
                  <Loader2 className="w-8 h-8 animate-spin" />
                ) : (
                  <Mic className="w-8 h-8" />
                )}
              </button>
            </div>

            <p className="text-xs text-slate-400 font-medium">
              {isRecording 
                ? '🔴 Recording audio stream... Click to stop.' 
                : isTranscribing
                ? '⚡ Transcribing audio with Groq Whisper AI...'
                : hasRecorded 
                ? '✅ Audio transcribed successfully. You can edit below.' 
                : 'Click microphone to start speaking'}
            </p>
          </div>

          {/* Editable Live Transcript Box */}
          {(hasRecorded || isTranscribing) && (
            <div className="space-y-4 animate-in fade-in duration-300">
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                    <Edit3 className="w-3.5 h-3.5 text-sky-400" />
                    <span>Whisper Decoded Transcript (Editable)</span>
                  </label>
                  {detectedLanguage && (
                    <span className="text-[10px] font-mono bg-sky-500/20 text-sky-300 px-2 py-0.5 rounded">
                      Language: {detectedLanguage}
                    </span>
                  )}
                </div>

                {isTranscribing ? (
                  <div className="w-full px-4 py-8 bg-slate-900 border border-slate-700 rounded-xl flex items-center justify-center gap-2 text-xs text-sky-300">
                    <Loader2 className="w-4 h-4 animate-spin text-sky-400" />
                    <span>Transcribing your speech via Groq Whisper...</span>
                  </div>
                ) : (
                  <textarea
                    rows={3}
                    value={transcript}
                    onChange={(e) => setTranscript(e.target.value)}
                    placeholder="Speak into microphone or edit the transcribed text here..."
                    className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-xs sm:text-sm text-slate-200 leading-relaxed font-sans focus:outline-none focus:border-sky-500"
                  />
                )}
              </div>

              {/* Location input with GPS button */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-semibold text-slate-300">
                    Location / Landmark
                  </label>
                  <button
                    type="button"
                    onClick={handleGetCurrentLocation}
                    disabled={isLocating}
                    className="text-[11px] text-sky-400 hover:underline flex items-center gap-1"
                  >
                    <Navigation className={`w-3 h-3 ${isLocating ? 'animate-spin' : ''}`} />
                    <span>Use Detected GPS</span>
                  </button>
                </div>
                <div className="relative">
                  <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                  <input
                    type="text"
                    value={locationText}
                    onChange={(e) => setLocationText(e.target.value)}
                    placeholder="e.g. 4th Cross, Green Park Extension, Ward 09"
                    className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs sm:text-sm text-white focus:outline-none focus:border-sky-500 font-mono"
                  />
                </div>
              </div>

              <button
                type="button"
                onClick={handleProcessVoice}
                disabled={isProcessing || isTranscribing || isRecording || !transcript.trim()}
                className={`w-full py-3 rounded-xl font-bold text-xs sm:text-sm flex items-center justify-center gap-2 shadow-lg transition-all ${
                  isProcessing || isTranscribing || isRecording || !transcript.trim()
                    ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                    : 'bg-gradient-to-r from-sky-500 to-cyan-400 hover:from-sky-400 hover:to-cyan-300 text-slate-950 shadow-sky-500/25'
                }`}
              >
                {isProcessing ? (
                  <>
                    <Sparkles className="w-4 h-4 animate-spin text-slate-950" />
                    <span>Processing Voice Grievance with AI...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 text-slate-950" />
                    <span>Process & Register Voice Complaint</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Output & Triage Result */}
        <div className="lg:col-span-5 space-y-6">
          {resultComplaint ? (
            <div className="glass-panel-glow p-6 rounded-3xl space-y-6 animate-in fade-in duration-300">
              {/* Duplicate Notice Banner if Linked */}
              {resultComplaint.duplicate_link_info?.is_duplicate && (
                <div className="p-4 rounded-2xl bg-amber-500/15 border border-amber-500/30 text-amber-300 space-y-2">
                  <div className="flex items-center gap-2 font-bold text-xs">
                    <Users className="w-4 h-4 text-amber-400" />
                    <span>Possible Existing Civic Issue Detected</span>
                  </div>
                  <p className="text-xs text-slate-200">
                    Linked to primary complaint: <strong className="font-mono text-white">{resultComplaint.duplicate_link_info.primary_complaint_id}</strong> (Similarity: {Math.round(resultComplaint.duplicate_link_info.similarity * 100)}%)
                  </p>
                  <p className="text-[11px] text-amber-300/80">
                    Citizen reports: <strong>{resultComplaint.duplicate_link_info.report_count}</strong>. Additional reports strengthen municipal dispatch priority.
                  </p>
                </div>
              )}

              <div className="flex items-start justify-between pb-4 border-b border-slate-800">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                    {resultComplaint.duplicate_link_info?.is_duplicate ? 'Voice Linked Ticket' : 'Voice Ticket Registered'}
                  </span>
                  <h3 className="text-xl font-black text-white font-mono">
                    {resultComplaint.complaint_id}
                  </h3>
                </div>
                <StatusBadge status={resultComplaint.status} size="sm" />
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block font-mono">Category</span>
                    <span className="text-xs font-bold text-white uppercase">{resultComplaint.category}</span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block font-mono">Audio Language</span>
                    <span className="text-xs font-bold text-sky-400">{resultComplaint.language || 'English'}</span>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800">
                  <RiskGauge 
                    score={resultComplaint.risk_score} 
                    priority={resultComplaint.priority}
                    reasons={resultComplaint.risk_reasons || []}
                  />
                </div>

                <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1">
                  <span className="text-[10px] uppercase font-mono font-bold text-slate-400">Assigned Department</span>
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-100">
                    <Building2 className="w-4 h-4 text-civic-400" />
                    <span>{resultComplaint.department || resultComplaint.external_service_name}</span>
                  </div>
                </div>

                <AgentTraceViewer trace={resultComplaint.agent_trace} />

                <button
                  onClick={() => {
                    setTrackSearchId(resultComplaint.complaint_id);
                    setActivePage('track');
                  }}
                  className="w-full py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs flex items-center justify-center gap-2 transition-colors shadow-md shadow-sky-500/20"
                >
                  <span>Track Resolution Progress</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ) : (
            <div className="glass-panel p-8 rounded-3xl border border-slate-800 text-center space-y-4">
              <div className="w-14 h-14 mx-auto rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500">
                <Mic className="w-6 h-6 text-sky-400/60" />
              </div>
              <h3 className="text-base font-bold text-white">
                Multilingual Speech Pipeline
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Click the microphone to record a complaint in Telugu, Hindi, Tamil, Kannada, or English. The backend uses Whisper STT + Groq LLM + Python deterministic rules.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
