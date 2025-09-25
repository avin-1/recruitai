import React from 'react';
import { Candidate } from '../../types';
import Modal from '../ui/Modal';
import Button from '../ui/Button';

interface CandidateProfileModalProps {
  candidate: Candidate;
  onClose: () => void;
}

const CandidateProfileModal: React.FC<CandidateProfileModalProps> = ({ candidate, onClose }) => {
  const getScoreColor = (score: number) => {
    if (score > 90) return 'bg-green-500/10 text-green-400';
    if (score > 80) return 'bg-yellow-500/10 text-yellow-400';
    return 'bg-orange-500/10 text-orange-400';
  };

  return (
    <Modal title="Candidate Profile" onClose={onClose}>
      <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-6">
        <img
          src={candidate.avatarUrl}
          alt={candidate.name}
          className="h-24 w-24 rounded-full object-cover mx-auto sm:mx-0 flex-shrink-0"
        />
        <div className="mt-4 sm:mt-0 text-center sm:text-left">
          <h3 className="text-xl font-bold text-white">{candidate.name}</h3>
          <p className="text-sm text-slate-400">{candidate.email}</p>
          <div className="mt-2 flex items-center justify-center sm:justify-start space-x-4">
            <span className={`inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium ${getScoreColor(candidate.matchScore)}`}>
              Match Score: {candidate.matchScore}%
            </span>
            <span className="inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium bg-indigo-500/10 text-indigo-400">
              {candidate.stage}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-6 border-t border-slate-700 pt-6">
        <div className="flex justify-between items-center">
            <h4 className="text-lg font-semibold text-slate-200">AI-Generated Resume Summary</h4>
            {candidate.resumeUrl && (
                <a 
                    href={candidate.resumeUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-sm font-medium text-indigo-400 hover:text-indigo-500"
                >
                    View Resume &rarr;
                </a>
            )}
        </div>
        <p className="mt-2 text-slate-400">
          {candidate.resumeSummary}
        </p>
      </div>

      {candidate.interviewNotes && (
        <div className="mt-6 border-t border-slate-700 pt-6">
            <h4 className="text-lg font-semibold text-slate-200">Interview Notes</h4>
            <p className="mt-2 text-slate-400 whitespace-pre-wrap">
                {candidate.interviewNotes}
            </p>
        </div>
      )}

      {/* Placeholder for future email actions */}
      <div className="mt-6 border-t border-slate-700 pt-4">
        <h4 className="text-sm font-medium text-slate-300 mb-2">Actions</h4>
        <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => alert('Feature coming soon!')}>Schedule Interview</Button>
            <Button variant="secondary" onClick={() => alert('Feature coming soon!')}>Send Offer</Button>
            <Button variant="secondary" onClick={() => alert('Feature coming soon!')}>Reject</Button>
        </div>
      </div>
    </Modal>
  );
};

export default CandidateProfileModal;