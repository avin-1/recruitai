import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Dashboard from './Dashboard';
import Home from './components/Home';
import FileUpload from './components/FileUpload';
import Profiles from './components/Profiles';
import Settings from './components/Settings';
import JobPortal from './components/JobPortal';
import Applicants from './components/Applicants';

function App() {
  return (
    <div className="flex flex-1 w-full h-full">
      <Dashboard>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/upload" element={<FileUpload />} />
          <Route path="/profiles" element={<Profiles />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/jobs" element={<JobPortal />} />
          <Route path="/applicants" element={<Applicants />} />
        </Routes>
      </Dashboard>
    </div>
  );
}

export default App;
