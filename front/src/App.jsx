import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Dashboard from './Dashboard';
import Home from './components/Home';
import CreateJobProfile from './components/CreateJobProfile';
import Profiles from './components/Profiles';
import Settings from './components/Settings';
import JobPortal from './components/JobPortal';
import Applicants from './components/Applicants';
import HRTestManager from './components/HRTestManager';
import CandidateTest from './components/CandidateTest';
import TestRoute from './components/TestRoute';
import InterviewScheduler from './components/InterviewScheduler';
import InterviewCandidates from './components/InterviewCandidates';
import AnalyticsDashboard from './components/AnalyticsDashboard';

function App() {
  return (
    <div className="flex flex-1 w-full h-full">
      <Routes>
        {/* Public route for candidate test */}
        <Route path="/test/:testId" element={<CandidateTest />} />
        {/* Test route to verify routing works */}
        <Route path="/test-route" element={<TestRoute />} />

        {/* Protected routes with Dashboard */}
        <Route path="/*" element={
          <Dashboard>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/upload" element={<CreateJobProfile />} />
              <Route path="/create-job-profile" element={<CreateJobProfile />} />
              <Route path="/profiles" element={<Profiles />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/jobs" element={<JobPortal />} />
              <Route path="/applicants" element={<Applicants />} />
              <Route path="/hr-tests" element={<HRTestManager />} />
              <Route path="/interviews" element={<InterviewScheduler />} />
              <Route path="/interview-candidates" element={<InterviewCandidates />} />
              <Route path="/analytics" element={<AnalyticsDashboard />} />
            </Routes>
          </Dashboard>
        } />
      </Routes>
    </div>
  );
}

export default App;
