import React, { useState, useMemo } from 'react';
import { Job, Candidate, PipelineStage } from './types';
import { mockJobs, mockCandidates } from './constants';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import PipelineView from './components/PipelineView';
import CandidateProfileModal from './components/modals/CandidateProfileModal';
import NewCandidateModal from './components/modals/NewCandidateModal';
import Sidebar from './components/Sidebar';
import JobDescriptionManagement from './components/views/JobDescriptionManagement';
import ResumeParsingView from './components/views/ResumeParsingView';
import ShortlistingView from './components/views/ShortlistingView';
import InterviewSchedulingView from './components/views/InterviewSchedulingView';
import FeedbackDashboardView from './components/views/FeedbackDashboardView';
import OtherJobsView from './components/views/OtherJobsView';
import ContactInfoView from './components/views/ContactInfoView';

type View = 'dashboard' | 'job-descriptions' | 'resume-parsing' | 'shortlisting' | 'interview-scheduling' | 'feedback' | 'other-jobs' | 'contact';

export default function App() {
  const [jobs, setJobs] = useState<Job[]>(mockJobs);
  const [candidates, setCandidates] = useState<Candidate[]>(mockCandidates);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [currentView, setCurrentView] = useState<View>('job-descriptions');
  const [isNewCandidateModalOpen, setIsNewCandidateModalOpen] = useState(false);

  const selectedJob = useMemo(() => {
    return jobs.find(job => job.id === selectedJobId) || null;
  }, [jobs, selectedJobId]);

  const selectedCandidate = useMemo(() => {
    return candidates.find(c => c.id === selectedCandidateId) || null;
  }, [candidates, selectedCandidateId]);

  const candidatesForSelectedJob = useMemo(() => {
    return candidates.filter(c => c.jobId === selectedJobId);
  }, [candidates, selectedJobId]);

  const handleSelectJob = (jobId: string) => {
    setSelectedJobId(jobId);
    // This will cause the content to render PipelineView
  };
  
  const handleBackToDashboard = () => {
    setSelectedJobId(null);
    setCurrentView('dashboard');
  };
  
  const handleViewCandidate = (candidateId: string) => {
    setSelectedCandidateId(candidateId);
  };
  
  const handleCloseCandidateModal = () => {
    setSelectedCandidateId(null);
  };

  const handleAddNewCandidate = (newCandidateData: Omit<Candidate, 'id' | 'jobId'>) => {
    if (!selectedJobId) return;

    const newCandidate: Candidate = {
      ...newCandidateData,
      id: `cand-${Date.now()}`,
      jobId: selectedJobId,
    };
    setCandidates(prev => [newCandidate, ...prev]);
    setIsNewCandidateModalOpen(false);
  };

  const updateCandidateStage = (candidateId: string, newStage: PipelineStage) => {
    setCandidates(prev => 
      prev.map(c => c.id === candidateId ? { ...c, stage: newStage } : c)
    );
  };

  const handleNavigate = (view: View) => {
    setSelectedJobId(null); // Deselect job when navigating away
    setCurrentView(view);
    setSidebarOpen(false); // Close sidebar on mobile after navigation
  }

  const renderContent = () => {
    if (selectedJobId && selectedJob) {
       return (
        <PipelineView 
          job={selectedJob} 
          candidates={candidatesForSelectedJob}
          onBack={handleBackToDashboard}
          onViewCandidate={handleViewCandidate}
          onUpdateCandidateStage={updateCandidateStage}
          onAddCandidate={() => setIsNewCandidateModalOpen(true)}
        />
       )
    }

    switch (currentView) {
      case 'dashboard':
        return <Dashboard jobs={jobs} candidates={candidates} onSelectJob={handleSelectJob} />;
      case 'job-descriptions':
        return <JobDescriptionManagement />;
      case 'resume-parsing':
        return <ResumeParsingView />;
      case 'shortlisting':
        return <ShortlistingView />;
      case 'interview-scheduling':
        return <InterviewSchedulingView />;
      case 'feedback':
         return <FeedbackDashboardView />;
      case 'other-jobs':
        return <OtherJobsView />;
      case 'contact':
        return <ContactInfoView />;
      default:
        return <Dashboard jobs={jobs} candidates={candidates} onSelectJob={handleSelectJob} />;
    }
  }

  return (
    <div className="flex h-screen bg-slate-900 text-slate-200">
      <Sidebar 
        isOpen={isSidebarOpen} 
        setOpen={setSidebarOpen} 
        currentView={currentView}
        onNavigate={handleNavigate}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header 
          onMenuClick={() => setSidebarOpen(!isSidebarOpen)}
          currentView={currentView}
          breadcrumbs={selectedJob ? ['Dashboard', selectedJob.title] : [currentView]}
        />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-slate-900 p-4 sm:p-6 lg:p-8">
          {renderContent()}
        </main>
      </div>
      
      {selectedCandidate && (
        <CandidateProfileModal
          candidate={selectedCandidate}
          onClose={handleCloseCandidateModal}
        />
      )}
      {isNewCandidateModalOpen && (
        <NewCandidateModal 
          onClose={() => setIsNewCandidateModalOpen(false)}
          onAddCandidate={handleAddNewCandidate}
        />
      )}
    </div>
  );
}