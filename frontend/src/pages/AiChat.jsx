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
  AlertTriangle
} from 'lucide-react';
import { useComplaints } from '../context/ComplaintContext';
import PriorityBadge from '../components/PriorityBadge';
import StatusBadge from '../components/StatusBadge';
import RiskGauge from '../components/RiskGauge';

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
  const [collectedData, setCollectedData] = useState({ issueText: '', location: '', coords: null });
  const chatContainerRef = useRef(null);
  const isFirstRender = useRef(true);

  const quickPrompts = [
    "Huge pothole outside community center on 100ft road, bikes slipping",
    "Garbage dump not cleared for past 5 days in Sector 9, foul smell",
    "Drinking water pipeline burst near metro pillar 42, road flooded",
    "Someone sent me a fraudulent text asking for bank OTP",
    "3 streetlights on Park View Avenue are pitch black at night"
  ];

  // Prevent auto-scrolling the whole window on mount; only scroll internal chat box on new user/bot messages
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
  }, [messages, isTyping]);

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
    setIsTyping(true);

    const queryLower = query.toLowerCase();

    // Check if the input is very short/vague and missing location
    const isVague = query.trim().split(/\s+/).length <= 4 && !collectedData.issueText;
    const hasLocation = queryLower.includes('ward') || queryLower.includes('road') || queryLower.includes('near') || queryLower.includes('street') || queryLower.includes('gps') || collectedData.location;

    if (isVague && !hasLocation) {
      setTimeout(() => {
        setCollectedData(prev => ({ ...prev, issueText: query }));
        const aiMsg = {
          id: Date.now() + 1,
          sender: 'ai',
          text: `I understand: "${query}". To ensure rapid dispatch to the correct field crew, **where is this located?** You can type an address/landmark or click "Share Current Location" below.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages(prev => [...prev, aiMsg]);
        setIsTyping(false);
      }, 700);
      return;
    }

    // Process submission
    try {
      const fullText = collectedData.issueText ? `${collectedData.issueText}. Location details: ${query}` : query;
      const result = await submitNewComplaint({
        complaintText: fullText,
        locationText: collectedData.location || (queryLower.includes('on') || queryLower.includes('in') || queryLower.includes('near') ? '' : ''),
        latitude: collectedData.coords?.lat,
        longitude: collectedData.coords?.lon,
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
                    `Your message has been linked as a **supporting report**, accelerating the dispatch priority for the response crew!`;
      } else if (result.domain === 'municipal') {
        replyText = `I have logged and triaged your issue to **${result.department}**.\n\n` +
                    `• **Ticket ID**: \`${result.complaint_id}\`\n` +
                    `• **Safety Risk Score**: **${result.risk_score}/100 (${result.priority} priority)**\n` +
                    `• **Committed SLA**: **${result.sla_hours} hours**\n\n` +
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
      setCollectedData({ issueText: '', location: '', coords: null });
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
    setCollectedData({ issueText: '', location: '', coords: null });
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
            Conversational intake assistant with confidence-aware clarification and deterministic risk routing.
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
        <div className="lg:col-span-8 bg-white rounded-3xl overflow-hidden flex flex-col h-[640px] border border-slate-200 shadow-md">
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
              placeholder="Describe your issue or ask a civic question..."
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
                  Chat conversationally with CivicResolve. Missing details like location are clarified before final dispatch.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
