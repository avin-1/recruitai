import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import NotificationCenter from './components/NotificationCenter';
import { SHORTLISTING_API_BASE, INTERVIEW_API_BASE } from '@/lib/apiConfig';

function Dashboard({ children }) {
  const [notifications, setNotifications] = useState([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    loadNotifications();
    const interval = setInterval(loadNotifications, 3000); // Poll every 3 seconds
    return () => clearInterval(interval);
  }, []);

  const loadNotifications = async () => {
    try {
      // Try shortlisting service first
      let res = await fetch(`${SHORTLISTING_API_BASE}/notifications`);
      let data = await res.json();

      if (!data.success) {
        // Fallback to interview service
        res = await fetch(`${INTERVIEW_API_BASE}/notifications`);
        data = await res.json();
      }

      if (data.success) {
        setNotifications(data.notifications || []);
      }
    } catch (err) {
      // Try interview service as fallback
      try {
        const res = await fetch(`${INTERVIEW_API_BASE}/notifications`);
        const data = await res.json();
        if (data.success) {
          setNotifications(data.notifications || []);
        }
      } catch (err2) {
        // Silently fail if both services unavailable
        console.debug('Notifications unavailable from both services');
      }
    }
  };

  const handleClearNotification = async (index) => {
    try {
      // Try shortlisting service first, then interview service
      try {
        await fetch(`${SHORTLISTING_API_BASE}/notifications/${index}/read`, {
          method: 'POST'
        });
      } catch {
        await fetch(`${INTERVIEW_API_BASE}/notifications/${index}/read`, {
          method: 'POST'
        });
      }
      loadNotifications();
    } catch (err) {
      console.error('Error marking notification read:', err);
    }
  };

  const handleClearAll = async () => {
    try {
      // Try shortlisting service first, then interview service
      try {
        await fetch(`${SHORTLISTING_API_BASE}/notifications/clear`, {
          method: 'POST'
        });
      } catch {
        await fetch(`${INTERVIEW_API_BASE}/notifications/clear`, {
          method: 'POST'
        });
      }
      loadNotifications();
    } catch (err) {
      console.error('Error clearing notifications:', err);
    }
  };

  return (
    <div className="min-h-screen flex flex-col w-full relative overflow-hidden bg-slate-50">
      {/* Animated Background with Glassmorphism */}
      <div className="fixed inset-0 -z-10">
        {/* Gradient Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 opacity-80"></div>

        {/* Animated Blobs */}
        <div className="absolute top-0 -left-20 w-96 h-96 bg-blue-400/20 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob"></div>
        <div className="absolute top-0 -right-20 w-96 h-96 bg-purple-400/20 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-20 left-1/2 w-96 h-96 bg-indigo-400/20 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob animation-delay-4000"></div>

        {/* Glass Overlay */}
        <div className="absolute inset-0 bg-white/10 backdrop-blur-[100px]"></div>
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-col flex-1 h-screen overflow-hidden">
        <Navbar onMenuClick={() => setIsSidebarOpen(!isSidebarOpen)} />
        <div className="flex flex-1 w-full overflow-hidden">
          <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
          <main className="flex-1 overflow-y-auto overflow-x-hidden page-transition p-4 lg:p-8 scroll-smooth">
            <div className="max-w-[1600px] mx-auto">
              {children}
            </div>
          </main>
        </div>
      </div>

      <NotificationCenter
        notifications={notifications}
        onClear={handleClearNotification}
        onClearAll={handleClearAll}
      />
    </div>
  );
}

export default Dashboard;
