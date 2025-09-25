import React from 'react';
import { Candidate, PipelineStage } from '../types';
import CandidateCard from './CandidateCard';

interface KanbanColumnProps {
  stage: PipelineStage;
  candidates: Candidate[];
  onViewCandidate: (candidateId:string) => void;
}

const STAGE_COLORS: Record<PipelineStage, string> = {
    [PipelineStage.APPLIED]: 'border-t-sky-500',
    [PipelineStage.SCREENING]: 'border-t-blue-500',
    [PipelineStage.ASSESSMENT]: 'border-t-purple-500',
    [PipelineStage.INTERVIEW]: 'border-t-indigo-500',
    [PipelineStage.OFFER]: 'border-t-amber-500',
    [PipelineStage.HIRED]: 'border-t-green-500',
};


const KanbanColumn: React.FC<KanbanColumnProps> = ({ stage, candidates, onViewCandidate }) => {
  return (
    <div className={`flex-shrink-0 w-72 bg-slate-800 rounded-lg shadow-sm border-t-4 ${STAGE_COLORS[stage]}`}>
      <div className="p-4">
        <h3 className="text-md font-semibold text-slate-200 flex items-center justify-between">
          {stage}
          <span className="text-sm font-normal bg-slate-700 text-slate-300 rounded-full px-2 py-0.5">
            {candidates.length}
          </span>
        </h3>
        <div className="mt-4 space-y-3">
          {candidates.map(candidate => (
            <CandidateCard 
              key={candidate.id} 
              candidate={candidate} 
              onViewCandidate={onViewCandidate}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default KanbanColumn;