import React from 'react';
import { Job } from '../types';
import { UsersIcon } from './icons/UsersIcon';

interface JobCardProps {
  job: Job;
  candidateCount: number;
  onSelectJob: (jobId: string) => void;
}

const JobCard: React.FC<JobCardProps> = ({ job, candidateCount, onSelectJob }) => {
  const statusColor = job.status === 'Open' ? 'bg-green-500/10 text-green-400' : 'bg-slate-500/10 text-slate-400';

  return (
    <div 
      onClick={() => onSelectJob(job.id)}
      className="bg-slate-800 rounded-lg shadow-lg overflow-hidden transform hover:-translate-y-1 transition-transform duration-300 cursor-pointer border border-slate-700 hover:border-indigo-500"
    >
      <div className="p-6">
        <div className="flex justify-between items-start">
          <span className={`inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium ${statusColor}`}>
            {job.status}
          </span>
        </div>
        <div className="mt-4">
          <h3 className="text-xl font-semibold text-white truncate">{job.title}</h3>
          <p className="mt-1 text-slate-400">{job.department}</p>
        </div>
      </div>
      <div className="border-t border-slate-700 px-6 py-4 bg-slate-800/50">
        <div className="flex items-center justify-between text-sm text-slate-300">
          <div className="flex items-center">
            <UsersIcon className="h-5 w-5 mr-2 text-slate-400" />
            <span>{candidateCount} Candidates</span>
          </div>
          <span className="text-indigo-400 font-semibold hover:text-indigo-300">
            View Pipeline &rarr;
          </span>
        </div>
      </div>
    </div>
  );
};

export default JobCard;