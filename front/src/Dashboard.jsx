import React from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

function Dashboard({ children }) {
  return (
    <div className="min-h-screen flex flex-col bg-gray-100 w-full">
      <Navbar />
      <div className="flex flex-1 w-full">
        <Sidebar />
        {children}
      </div>
    </div>
  );
}

export default Dashboard;
