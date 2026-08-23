import React, { useState, useEffect } from 'react';
import { ComplaintProvider } from './context/ComplaintContext';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Footer from './components/Footer';
import Home from './pages/Home';
import ReportIssue from './pages/ReportIssue';
import AiChat from './pages/AiChat';
import TrackComplaint from './pages/TrackComplaint';
import AuthorityDashboard from './pages/AuthorityDashboard';

export default function App() {
  const [activePage, setActivePage] = useState('home');
  const [trackSearchId, setTrackSearchId] = useState('');

  // Always reset window scroll position to the top when navigating between pages
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }, [activePage]);

  return (
    <ComplaintProvider>
      <div className="min-h-screen flex flex-col bg-[#f8fafc] text-slate-800 selection:bg-red-500/20 selection:text-red-700">
        {/* Top Header */}
        <Navbar activePage={activePage} setActivePage={setActivePage} />

        {/* Main Body Layout with Vertical Left Navigation attached directly to left edge */}
        <div className="flex-1 flex w-full">
          {/* Vertical Left Navigation Sidebar */}
          <Sidebar activePage={activePage} setActivePage={setActivePage} />

          {/* Dynamic Page Router Container */}
          <main className="flex-1 min-w-0 px-4 sm:px-6 lg:px-8 py-6">
            {activePage === 'home' && (
              <Home 
                setActivePage={setActivePage} 
                setTrackSearchId={setTrackSearchId} 
              />
            )}

            {activePage === 'report' && (
              <ReportIssue 
                setActivePage={setActivePage} 
                setTrackSearchId={setTrackSearchId} 
              />
            )}

            {activePage === 'chat' && (
              <AiChat 
                setActivePage={setActivePage} 
                setTrackSearchId={setTrackSearchId} 
              />
            )}

            {activePage === 'track' && (
              <TrackComplaint 
                initialSearchId={trackSearchId} 
                setActivePage={setActivePage} 
              />
            )}

            {activePage === 'authority' && (
              <AuthorityDashboard 
                setActivePage={setActivePage} 
                setTrackSearchId={setTrackSearchId} 
              />
            )}
          </main>
        </div>

        {/* Global Footer */}
        <Footer setActivePage={setActivePage} />
      </div>
    </ComplaintProvider>
  );
}
