import React, { useState, useRef, useEffect } from 'react';
import { 
  MessageSquareCode, 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  ArrowRight, 
  RotateCcw, 
  Navigation, 
  CheckCircle2, 
  AlertCircle, 
  Users, 
  AlertTriangle,
  Upload,
  Image as ImageIcon,
  X,
  Camera,
  Check
} from 'lucide-react';
import { useComplaints } from '../context/ComplaintContext';
import PriorityBadge from '../components/PriorityBadge';
import StatusBadge from '../components/StatusBadge';
import RiskGauge from '../components/RiskGauge';

const normalizeChatText = (value = '') =>
  value
    .toLowerCase()
    .replace(/[^\w\s']/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const getBasicChatReply = (rawText) => {
  const text = normalizeChatText(rawText);

  if (!text) return null;

  const greetings = [
    'hi',
    'hello',
    'hey',
    'hii',
    'hiii',
    'hello there'
  ];

  if (greetings.includes(text)) {
    return "Hello! I'm CivicResolve AI. I can help you report a civic issue, identify the responsible department, check an existing complaint, or guide you through the reporting process.";
  }

  if (
    text === 'good morning' ||
    text === 'morning'
  ) {
    return "Good morning! How can I help with a civic issue today?";
  }

  if (
    text === 'good afternoon' ||
    text === 'afternoon'
  ) {
    return "Good afternoon! Tell me about the civic issue you'd like help with.";
  }

  if (
    text === 'good evening' ||
    text === 'evening'
  ) {
    return "Good evening! How can CivicResolve help you today?";
  }

  if (
    [
      'thanks',
      'thank you',
      'thankyou',
      'thanks a lot',
      'thank you so much'
    ].includes(text)
  ) {
    return "You're welcome. I'm here whenever you need help with a civic complaint.";
  }

  if (
    [
      'bye',
      'goodbye',
      'see you',
      'see you later'
    ].includes(text)
  ) {
    return "Goodbye! If you need to report or track a civic issue later, CivicResolve will be here to help.";
  }

  if (
    [
      'help',
      'what can you do',
      'what do you do',
      'how can you help'
    ].includes(text)
  ) {
    return "I can help you report civic problems such as potholes, garbage, drainage, water supply, streetlights and damaged infrastructure. I can also help identify the responsible department and guide you to track an existing complaint.";
  }

  return null;
};

const isAffirmativeResponse = (text) => {
  const t = normalizeChatText(text);
  const affirmations = [
    'yes',
    'yeah',
    'yep',
    'yes please',
    'yes do it',
    'sure',
    'okay',
    'ok',
    'upload',
    'add photo',
    'i have a photo',
    'attach photo',
    'photo',
    'i have photo',
    'with photo',
    'take photo'
  ];
  return affirmations.includes(t) || t.startsWith('yes') || t.includes('upload') || t.includes('attach');
};

const isNegativeResponse = (text) => {
  const t = normalizeChatText(text);
  const negations = [
    'no',
    'no thanks',
    'skip',
    'not now',
    "i don't have one",
    "i dont have one",
    'continue without photo',
    'no photo',
    'without photo',
    'none',
    'nope',
    'nah',
    'dont have'
  ];
  return negations.includes(t) || t.startsWith('no') || t.includes('skip') || t.includes('without');
};

export default function AiChat({ setActivePage, setTrackSearchId }) {
  const { submitNewComplaint } = useComplaints();

  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'ai',
      text: "Hello! I'm CivicResolve AI, your intelligent civic triage assistant. Describe any civic issue or hazard in your neighborhood.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
  ]);

  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [extractedComplaint, setExtractedComplaint] = useState(null);
  
  // Conversational state
  const [collectedData, setCollectedData] = useState({
    issueText: '',
    location: '',
    coords: null,
    awaitingLocation: false,
    awaitingPhotoDecision: false,
    awaitingPhotoUpload: false,
    photoFile: null,
    photoPreview: null
  });

  const chatContainerRef = useRef(null);
  const isFirstRender = useRef(true);
  const fileInputRef = useRef(null);

  const quickPrompts = [
    "Huge pothole outside community center on 100ft road, bikes slipping",
    "Garbage dump not cleared for past 5 days in Sector 9, foul smell",
    "Drinking water pipeline burst near metro pillar 42, road flooded",
    "Someone sent me a fraudulent text asking for bank OTP",
    "3 streetlights on Park View Avenue are pitch black at night"
  ];

  // Auto-scroll chat container on new message or typing state
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages, isTyping, collectedData.awaitingPhotoUpload, collectedData.awaitingPhotoDecision]);

  const handleShareLocation = () => {
    if (!navigator.geolocation) {
      handleSendMessage("My location is Ward 14, Central Zone");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = parseFloat(pos.coords.latitude.toFixed(5));
        const lon = parseFloat(pos.coords.longitude.toFixed(5));
        setCollectedData(prev => ({ ...prev, coords: { lat, lon }, location: `GPS: ${lat}, ${lon}` }));
        handleSendMessage(`My current location is GPS: ${lat}, ${lon}`);
      },
      () => {
        handleSendMessage("My location is Ward 14, Central Zone");
      }
    );
  };

  // Canonical submission function
  const executeComplaintSubmission = async (issueText, locationText, coords, imageFile) => {
    setIsTyping(true);
    try {
      const result = await submitNewComplaint({
        complaintText: issueText,
        locationText: locationText || '',
        latitude: coords?.lat,
        longitude: coords?.lon,
        image: imageFile,
        sourceChannel: 'chat',
        citizenName: 'Chat Citizen',
      });

      setExtractedComplaint(result);

      let replyText = '';
      if (result.duplicate_link_info?.is_duplicate) {
        const dup = result.duplicate_link_info;
        replyText = `⚠️ **Probable Duplicate Civic Issue Detected**\n\n` +
                    `An existing municipal ticket for this grievance is already registered under **\`${dup.primary_complaint_id}\`** (${Math.round(dup.similarity * 100)}% match).\n\n` +
                    `• **Primary Ticket**: \`${dup.primary_complaint_id}\`\n` +
                    `• **Citizen Reports Count**: **${dup.report_count}**\n` +
                    `• **Department**: **${result.department}**\n` +
                    `• **Prioritized Risk Score**: **${result.risk_score}/100 (${result.priority} priority)**\n` +
                    `• **SLA Target**: **${result.sla_hours} hours**\n\n` +
                    `Your grievance ${imageFile ? 'and photo evidence ' : ''}have been linked as a **supporting report**, accelerating dispatch priority for municipal crews!`;
      } else if (result.domain === 'municipal') {
        replyText = `I have logged and triaged your grievance to **${result.department}**.\n\n` +
                    `• **Ticket ID**: \`${result.complaint_id}\`\n` +
                    `• **Safety Risk Score**: **${result.risk_score}/100 (${result.priority} priority)**\n` +
                    `• **Committed SLA**: **${result.sla_hours} hours**\n\n` +
                    (imageFile ? `• **Visual Evidence Attached**: 1 Photo processed.\n\n` : '') +
                    `Your official tracking reference card is ready below.`;
      } else if (result.domain === 'emergency') {
        replyText = `⚠️ **URGENT SAFETY ROUTING:** This appears to be an immediate emergency. CivicResolve has routed this to **${result.external_service_name || 'ERSS 112'}**.`;
      } else {
        replyText = `CivicResolve identified that this is a **${result.service_type || 'public service'}** matter falling under **${result.external_service_name || 'Verified Public Authority'}** rather than municipal works. Official referral prepared below.`;
      }

      const aiMsg = {
        id: Date.now() + 1,
        sender: 'ai',
        text: replyText,
        complaintData: result,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages(prev => [...prev, aiMsg]);
      setCollectedData({
        issueText: '',
        location: '',
        coords: null,
        awaitingLocation: false,
        awaitingPhotoDecision: false,
        awaitingPhotoUpload: false,
        photoFile: null,
        photoPreview: null
      });
    } catch (err) {
      console.error("AI Chat error:", err);
      const errMsg = {
        id: Date.now() + 1,
        sender: 'ai',
        text: `⚠️ Error submitting to backend: ${err.message}. Please check backend connection.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  // Photo handlers
  const handlePhotoSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 8 * 1024 * 1024) {
      alert("Please upload an image smaller than 8MB.");
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      setCollectedData(prev => ({
        ...prev,
        photoFile: file,
        photoPreview: reader.result
      }));
    };
    reader.readAsDataURL(file);
  };

  const handleRemovePhoto = () => {
    setCollectedData(prev => ({
      ...prev,
      photoFile: null,
      photoPreview: null
    }));
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleConfirmPhotoSubmit = () => {
    const { issueText, location, coords, photoFile } = collectedData;
    executeComplaintSubmission(issueText, location, coords, photoFile);
  };

  const handleChooseYesPhoto = () => {
    setCollectedData(prev => ({
      ...prev,
      awaitingPhotoDecision: false,
      awaitingPhotoUpload: true
    }));
    const aiMsg = {
      id: Date.now(),
      sender: 'ai',
      text: "Please upload your photo evidence below (JPG, PNG, or WebP up to 8MB), then click Submit.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages(prev => [...prev, aiMsg]);
  };

  const handleChooseNoPhoto = () => {
    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: "No, continue without photo",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    const aiMsg = {
      id: Date.now() + 1,
      sender: 'ai',
      text: "No problem. We can continue without a photo.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages(prev => [...prev, userMsg, aiMsg]);
    const { issueText, location, coords } = collectedData;
    executeComplaintSubmission(issueText, location, coords, null);
  };

  const handleSendMessage = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim()) return;

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');

    // 1. Basic deterministic conversational replies
    const basicReply = getBasicChatReply(query);
    if (basicReply) {
      setIsTyping(true);
      setTimeout(() => {
        const aiMsg = {
          id: Date.now() + 1,
          sender: 'ai',
          text: basicReply,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages(prev => [...prev, aiMsg]);
        setIsTyping(false);
      }, 350);
      return;
    }

    // 2. If awaiting photo decision (Yes/No response)
    if (collectedData.awaitingPhotoDecision) {
      if (isAffirmativeResponse(query)) {
        handleChooseYesPhoto();
        return;
      }
      if (isNegativeResponse(query)) {
        setIsTyping(true);
        setTimeout(() => {
          const aiMsg = {
            id: Date.now() + 1,
            sender: 'ai',
            text: "No problem. We can continue without a photo.",
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          };
          setMessages(prev => [...prev, aiMsg]);
          executeComplaintSubmission(collectedData.issueText, collectedData.location, collectedData.coords, null);
        }, 300);
        return;
      }
    }

    // 3. If awaiting location response
    if (collectedData.awaitingLocation) {
      setIsTyping(true);
      setTimeout(() => {
        const fullIssueText = collectedData.issueText;
        const newLocation = query;
        setCollectedData(prev => ({
          ...prev,
          location: newLocation,
          awaitingLocation: false,
          awaitingPhotoDecision: true
        }));

        const aiMsg = {
          id: Date.now() + 1,
          sender: 'ai',
          text: `Got it, location recorded as: **${newLocation}**.\n\nWould you like to attach a photo as evidence?\nYou can upload a photo now, or reply **No** to continue without one.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isPhotoPrompt: true
        };
        setMessages(prev => [...prev, aiMsg]);
        setIsTyping(false);
      }, 500);
      return;
    }

    // 4. Initial Complaint Input
    const queryLower = query.toLowerCase();
    const isVague = query.trim().split(/\s+/).length <= 4;
    const hasLocationWords = queryLower.includes('ward') || queryLower.includes('road') || queryLower.includes('near') || queryLower.includes('street') || queryLower.includes('gps') || queryLower.includes('sector') || queryLower.includes('cross') || queryLower.includes('nagar') || queryLower.includes('junction') || queryLower.includes('pillar') || queryLower.includes('colony');

    if (isVague && !hasLocationWords && !collectedData.location) {
      setIsTyping(true);
      setTimeout(() => {
        setCollectedData(prev => ({
          ...prev,
          issueText: query,
          awaitingLocation: true,
          awaitingPhotoDecision: false
        }));
        const aiMsg = {
          id: Date.now() + 1,
          sender: 'ai',
          text: `I understand: "${query}". To ensure rapid dispatch to the correct field crew, **where is this located?** You can type an address/landmark or click "Share Location" above.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages(prev => [...prev, aiMsg]);
        setIsTyping(false);
      }, 600);
      return;
    }

    // Has issue and location -> Ask for photo evidence
    setIsTyping(true);
    setTimeout(() => {
      setCollectedData(prev => ({
        ...prev,
        issueText: query,
        location: collectedData.location || '',
        awaitingLocation: false,
        awaitingPhotoDecision: true
      }));

      const aiMsg = {
        id: Date.now() + 1,
        sender: 'ai',
        text: `I have analyzed your report.\n\nWould you like to attach a photo as evidence?\nYou can upload a photo now, or reply **No** to continue without one.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isPhotoPrompt: true
      };
      setMessages(prev => [...prev, aiMsg]);
      setIsTyping(false);
    }, 600);
  };

  const handleResetChat = () => {
    setMessages([
      {
        id: 1,
        sender: 'ai',
        text: "Hello! I'm CivicResolve AI, your intelligent civic triage assistant. Describe any civic issue or hazard in your neighborhood.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
    ]);
    setExtractedComplaint(null);
    setCollectedData({
      issueText: '',
      location: '',
      coords: null,
      awaitingLocation: false,
      awaitingPhotoDecision: false,
      awaitingPhotoUpload: false,
      photoFile: null,
      photoPreview: null
    });
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-50 border border-red-200 text-red-700 text-xs font-bold mb-2">
            <MessageSquareCode className="w-3.5 h-3.5" />
            <span>Interactive Conversational Triage</span>
          </div>
          <h1 className="text-3xl font-black text-[#162044]">
            CivicResolve AI Chat
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 font-medium">
            Conversational intake assistant with confidence-aware clarification, photo evidence collection, and deterministic risk routing.
          </p>
        </div>

        <button
          onClick={handleResetChat}
          className="self-start sm:self-auto px-3.5 py-2 rounded-xl bg-white border border-slate-200 text-xs font-bold text-slate-700 hover:text-slate-900 hover:bg-slate-50 flex items-center gap-1.5 transition-colors shadow-sm"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Clear Conversation</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Chat Window */}
        <div className="lg:col-span-8 bg-white rounded-3xl overflow-hidden flex flex-col h-[660px] border border-slate-200 shadow-md">
          {/* Top Chat Bar */}
          <div className="bg-slate-50 border-b border-slate-200 px-6 py-3.5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-9 h-9 rounded-xl bg-red-100 border border-red-200 flex items-center justify-center text-red-600">
                  <Bot className="w-5 h-5" />
                </div>
                <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white"></span>
              </div>
              <div>
                <h3 className="text-xs font-black text-[#162044] flex items-center gap-2">
                  <span>CivicResolve Triage Bot</span>
                  <span className="text-[10px] font-mono text-emerald-700 bg-emerald-100 px-1.5 py-0.2 rounded font-bold">Online</span>
                </h3>
                <p className="text-[10px] text-slate-500 font-medium">Intake & Clarification Assistant</p>
              </div>
            </div>

            <button
              type="button"
              onClick={handleShareLocation}
              className="text-[11px] font-bold text-red-600 hover:text-red-700 px-2.5 py-1.5 rounded-lg bg-red-50 border border-red-200 flex items-center gap-1.5 transition-all"
            >
              <Navigation className="w-3 h-3 text-red-600" />
              <span>Share Location</span>
            </button>
          </div>

          {/* Messages Stream */}
          <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-6 space-y-4 max-h-[520px] bg-[#f8fafc]/50">
            {messages.map((msg) => {
              const isAi = msg.sender === 'ai';
              return (
                <div key={msg.id} className={`flex gap-3 ${isAi ? 'items-start' : 'items-start flex-row-reverse'}`}>
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                    isAi ? 'bg-red-50 text-red-600 border border-red-200' : 'bg-[#162044] text-white font-bold'
                  }`}>
                    {isAi ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
                  </div>

                  <div className="max-w-[82%] space-y-2">
                    <div className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                      isAi 
                        ? 'bg-white border border-slate-200 text-slate-800 shadow-sm' 
                        : 'bg-[#162044] text-white font-medium shadow-md'
                    }`}>
                      <div className="whitespace-pre-line">{msg.text}</div>

                      {/* Interactive Yes / No Photo buttons attached to photo prompt */}
                      {msg.isPhotoPrompt && collectedData.awaitingPhotoDecision && (
                        <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap gap-2">
                          <button
                            type="button"
                            onClick={handleChooseYesPhoto}
                            className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all"
                          >
                            <Camera className="w-3.5 h-3.5" />
                            <span>Yes, Attach Photo</span>
                          </button>
                          <button
                            type="button"
                            onClick={handleChooseNoPhoto}
                            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold flex items-center gap-1.5 border border-slate-300 transition-all"
                          >
                            <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                            <span>No, Continue Without Photo</span>
                          </button>
                        </div>
                      )}

                      {/* Attached Ticket Card if present */}
                      {msg.complaintData && (
                        <div className="mt-3 pt-3 border-t border-slate-200 space-y-2.5">
                          {/* Duplicate Detection Alert if linked */}
                          {msg.complaintData.duplicate_link_info?.is_duplicate && (
                            <div className="p-3 rounded-xl bg-amber-50 border border-amber-300 text-amber-900 space-y-1">
                              <div className="flex items-center gap-1.5 font-bold text-xs">
                                <Users className="w-3.5 h-3.5 text-amber-700" />
                                <span>Duplicate Detected — Supporting Report Linked</span>
                              </div>
                              <p className="text-[11px] text-slate-700">
                                Matched with existing ticket <strong className="font-mono text-slate-900">{msg.complaintData.duplicate_link_info.primary_complaint_id}</strong> ({Math.round(msg.complaintData.duplicate_link_info.similarity * 100)}% match). Total reports: <strong>{msg.complaintData.duplicate_link_info.report_count}</strong>.
                              </p>
                            </div>
                          )}

                          <div className="flex items-center justify-between font-mono text-[11px]">
                            <span className="text-slate-500 font-sans font-bold">
                              {msg.complaintData.duplicate_link_info?.is_duplicate ? 'Primary Ticket ID:' : 'Ticket ID:'}
                            </span>
                            <span className="text-red-600 font-bold">{msg.complaintData.complaint_id}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <PriorityBadge priority={msg.complaintData.priority} size="sm" />
                            <StatusBadge status={msg.complaintData.status} size="sm" />
                          </div>
                          <button
                            onClick={() => {
                              setTrackSearchId(msg.complaintData.complaint_id);
                              setActivePage('track');
                            }}
                            className="w-full py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold flex items-center justify-center gap-1.5 transition-colors border border-slate-300"
                          >
                            <span>Track {msg.complaintData.complaint_id}</span>
                            <ArrowRight className="w-3 h-3 text-red-600" />
                          </button>
                        </div>
                      )}
                    </div>
                    <span className="text-[10px] text-slate-400 block px-1 font-mono">{msg.timestamp}</span>
                  </div>
                </div>
              );
            })}

            {/* In-Chat Photo Upload Card (when user chose YES) */}
            {collectedData.awaitingPhotoUpload && (
              <div className="p-4 bg-white border-2 border-red-200 rounded-2xl shadow-md space-y-3 animate-in fade-in duration-200">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#162044] flex items-center gap-1.5">
                    <Camera className="w-4 h-4 text-red-600" />
                    <span>Attach Photo Evidence</span>
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">Max 8MB (JPG, PNG, WebP)</span>
                </div>

                {collectedData.photoPreview ? (
                  <div className="space-y-3">
                    <div className="relative rounded-xl overflow-hidden border border-slate-300 h-36 bg-slate-100">
                      <img src={collectedData.photoPreview} alt="Evidence preview" className="w-full h-full object-cover" />
                      <button
                        type="button"
                        onClick={handleRemovePhoto}
                        className="absolute top-2 right-2 p-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg shadow-sm"
                        title="Remove photo"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <div className="text-[11px] text-slate-600 font-mono truncate">
                      📎 {collectedData.photoFile?.name} ({(collectedData.photoFile?.size / 1024).toFixed(1)} KB)
                    </div>
                  </div>
                ) : (
                  <label className="border-2 border-dashed border-slate-300 hover:border-red-500 rounded-xl p-4 flex flex-col items-center justify-center cursor-pointer bg-slate-50 hover:bg-slate-100 transition-all">
                    <Upload className="w-6 h-6 text-slate-400 mb-1" />
                    <span className="text-xs font-bold text-slate-700">Click to choose image file</span>
                    <span className="text-[10px] text-slate-500">JPG, PNG, WebP supported</span>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      onChange={handlePhotoSelect}
                      className="hidden"
                    />
                  </label>
                )}

                <div className="flex items-center gap-2 pt-1">
                  <button
                    type="button"
                    onClick={handleConfirmPhotoSubmit}
                    className="flex-1 py-2 bg-[#e53935] hover:bg-[#d32f2f] text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 shadow-sm transition-all"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>{collectedData.photoFile ? 'Submit Grievance with Photo' : 'Submit Without Photo'}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setCollectedData(prev => ({ ...prev, awaitingPhotoUpload: false }));
                      executeComplaintSubmission(collectedData.issueText, collectedData.location, collectedData.coords, null);
                    }}
                    className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold border border-slate-300 transition-all"
                  >
                    Skip Photo
                  </button>
                </div>
              </div>
            )}

            {isTyping && (
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-red-50 text-red-600 border border-red-200 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="px-4 py-3 rounded-2xl bg-white border border-slate-200 shadow-sm flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-red-600 animate-bounce"></span>
                  <span className="w-2 h-2 rounded-full bg-red-600 animate-bounce [animation-delay:0.2s]"></span>
                  <span className="w-2 h-2 rounded-full bg-red-600 animate-bounce [animation-delay:0.4s]"></span>
                </div>
              </div>
            )}
          </div>

          {/* Quick Prompts Carousel */}
          <div className="px-6 py-2 bg-slate-50 border-t border-slate-200 overflow-x-auto flex gap-2 no-scrollbar">
            {quickPrompts.map((qp, i) => (
              <button
                key={i}
                onClick={() => handleSendMessage(qp)}
                className="whitespace-nowrap px-3 py-1 rounded-full bg-white hover:bg-slate-100 border border-slate-300 text-[11px] text-slate-700 hover:text-red-700 font-semibold transition-all shrink-0 shadow-xs"
              >
                + {qp.slice(0, 38)}...
              </button>
            ))}
          </div>

          {/* Chat Input Bar */}
          <form 
            onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
            className="p-4 bg-white border-t border-slate-200 flex items-center gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Describe your issue, reply Yes/No, or ask a question..."
              className="flex-1 px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-red-500 focus:bg-white transition-all shadow-inner"
            />

            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className={`p-2.5 rounded-xl font-bold transition-all ${
                input.trim() && !isTyping
                  ? 'bg-[#e53935] hover:bg-[#d32f2f] text-white shadow-md shadow-red-500/20'
                  : 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200'
              }`}
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>

        {/* Live Extraction Intelligence Sidebar */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-md space-y-4">
            <div className="flex items-center gap-2 text-xs font-black text-[#162044] pb-3 border-b border-slate-200">
              <Sparkles className="w-4 h-4 text-red-600" />
              <span>Real-Time Entity Extractor</span>
            </div>

            {extractedComplaint ? (
              <div className="space-y-4 text-xs animate-in fade-in duration-200">
                {extractedComplaint.duplicate_link_info?.is_duplicate && (
                  <div className="p-3 rounded-xl bg-amber-50 border border-amber-300 text-amber-900 space-y-1.5">
                    <div className="flex items-center gap-1.5 font-bold text-[11px]">
                      <Users className="w-3.5 h-3.5 text-amber-700" />
                      <span>DUPLICATE GRIEVANCE LINKED</span>
                    </div>
                    <p className="text-[11px] text-slate-800">
                      Matched existing ticket: <strong className="font-mono text-slate-900">{extractedComplaint.duplicate_link_info.primary_complaint_id}</strong>
                    </p>
                    <div className="flex justify-between text-[10px] text-amber-800 font-mono font-bold">
                      <span>Similarity: {Math.round(extractedComplaint.duplicate_link_info.similarity * 100)}%</span>
                      <span>Reports: {extractedComplaint.duplicate_link_info.report_count}</span>
                    </div>
                  </div>
                )}

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-[10px] uppercase font-mono font-bold text-slate-500 block">
                    {extractedComplaint.duplicate_link_info?.is_duplicate ? 'Linked Primary ID' : 'Registered ID'}
                  </span>
                  <span className="text-sm font-black text-red-600 font-mono">{extractedComplaint.complaint_id}</span>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-semibold">Domain:</span>
                    <span className="font-bold text-slate-900 uppercase">{extractedComplaint.domain}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-semibold">Category:</span>
                    <span className="font-bold text-slate-900 uppercase">{extractedComplaint.category}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-semibold">Confidence:</span>
                    <span className="font-mono text-emerald-700 font-black">{Math.round((extractedComplaint.confidence || 0.9) * 100)}%</span>
                  </div>
                </div>

                {extractedComplaint.domain === 'municipal' && (
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <RiskGauge 
                      score={extractedComplaint.risk_score} 
                      priority={extractedComplaint.priority}
                      reasons={extractedComplaint.risk_reasons}
                    />
                  </div>
                )}

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                  <span className="text-[10px] uppercase font-mono font-bold text-slate-500">Department</span>
                  <p className="font-bold text-slate-900">{extractedComplaint.department || extractedComplaint.external_service_name}</p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 space-y-2">
                <Bot className="w-8 h-8 text-slate-400 mx-auto" />
                <p className="text-xs text-slate-500 font-medium">
                  Chat conversationally with CivicResolve. Missing details like location and photo evidence are clarified before final dispatch.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
