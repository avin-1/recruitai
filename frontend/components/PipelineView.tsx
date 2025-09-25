import React from 'react';
import { Job, Candidate, PipelineStage } from '../types';
import KanbanBoard from './KanbanBoard';
import Button from './ui/Button';
import { PlusIcon } from './icons/PlusIcon';

interface PipelineViewProps {
  job: Job;
  candidates: Candidate[];
  onBack: () => void;
  onViewCandidate: (candidateId: string) => void;
  onUpdateCandidateStage: (candidateId: string, newStage: PipelineStage) => void;
  onAddCandidate: () => void;
}

const PipelineView: React.FC<PipelineViewProps> = ({ job, candidates, onBack, onViewCandidate, onUpdateCandidateStage, onAddCandidate }) => {
  return (
    <div className="flex flex-col h-full">
      <div className="mb-6">
        <Button onClick={onBack} variant="secondary" className="mb-4">
            &larr; Back to Dashboard
        </Button>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">{job.title}</h2>
                <p className="text-slate-400">{job.department}</p>
            </div>
            <div className="mt-4 sm:mt-0">
                <Button onClick={onAddCandidate} variant='primary'>
                    <PlusIcon className='h-5 w-5 mr-2'/>
                    Add Candidate
                </Button>
            </div>
        </div>
      </div>
      
      <div className="flex-grow overflow-x-auto">
        <KanbanBoard 
          candidates={candidates} 
          onViewCandidate={onViewCandidate}
          onUpdateCandidateStage={onUpdateCandidateStage}
        />
      </div>
    </div>
  );
};

export default PipelineView;