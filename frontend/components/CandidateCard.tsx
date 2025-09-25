import React from 'react';
import { Candidate } from '../types';

interface CandidateCardProps {
  candidate: Candidate;
  onViewCandidate: (candidateId: string) => void;
}

const CandidateCard: React.FC<CandidateCardProps> = ({ candidate, onViewCandidate }) => {
  const getScoreColor = (score: number) => {
    if (score > 90) return 'text-green-400';
    if (score > 80) return 'text-yellow-400';
    return 'text-orange-400';
  };

  return (
    <div 
      onClick={() => onViewCandidate(candidate.id)}
      className="bg-slate-700 p-3 rounded-lg shadow-md cursor-pointer hover:shadow-lg hover:ring-2 hover:ring-indigo-500 transition-all duration-200"
    >
      <div className="flex items-center space-x-3">
        <img 
          src={candidate.avatarUrl} 
          alt={candidate.name} 
          className="h-10 w-10 rounded-full object-cover" 
        />
        <div>
          <p className="text-sm font-semibold text-slate-100 truncate">{candidate.name}</p>
          <p className={`text-xs font-medium ${getScoreColor(candidate.matchScore)}`}>
            Match Score: {candidate.matchScore}%
          </p>
        </div>
      </div>
    </div>
  );
};

export default CandidateCard;