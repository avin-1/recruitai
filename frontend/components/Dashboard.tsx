import React from 'react';
import { Job, Candidate } from '../types';
import JobCard from './JobCard';

interface DashboardProps {
  jobs: Job[];
  candidates: Candidate[];
  onSelectJob: (jobId: string) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ jobs, candidates, onSelectJob }) => {
  return (
    <div>
      <h2 className="text-2xl font-bold tracking-tight text-white sm:text-3xl mb-6">
        Job Postings Dashboard
      </h2>
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {jobs.map(job => {
          const jobCandidates = candidates.filter(c => c.jobId === job.id);
          return (
            <JobCard 
              key={job.id} 
              job={job} 
              candidateCount={jobCandidates.length}
              onSelectJob={onSelectJob}
            />
          );
        })}
      </div>
    </div>
  );
};

export default Dashboard;