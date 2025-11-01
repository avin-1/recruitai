import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import NotificationCenter from './components/NotificationCenter';

function Dashboard({ children }) {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    loadNotifications();
    const interval = setInterval(loadNotifications, 3000); // Poll every 3 seconds
    return () => clearInterval(interval);
  }, []);

  const loadNotifications = async () => {
    try {
      // Try shortlisting service first (port 5001)
      let res = await fetch('http://localhost:5001/api/notifications');
      let data = await res.json();
      
      if (!data.success) {
        // Fallback to interview service (port 5002)
        res = await fetch('http://localhost:5002/api/notifications');
        data = await res.json();
      }
      
      if (data.success) {
        setNotifications(data.notifications || []);
      }
    } catch (err) {
      // Try interview service as fallback
      try {
        const res = await fetch('http://localhost:5002/api/notifications');
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
        await fetch(`http://localhost:5001/api/notifications/${index}/read`, {
          method: 'POST'
        });
      } catch {
        await fetch(`http://localhost:5002/api/notifications/${index}/read`, {
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
        await fetch('http://localhost:5001/api/notifications/clear', {
          method: 'POST'
        });
      } catch {
        await fetch('http://localhost:5002/api/notifications/clear', {
          method: 'POST'
        });
      }
      loadNotifications();
    } catch (err) {
      console.error('Error clearing notifications:', err);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-100 w-full">
      <Navbar />
      <div className="flex flex-1 w-full">
        <Sidebar />
        {children}
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
