
import React from 'react';
import { Candidate, PipelineStage } from '../types';
import { PIPELINE_STAGES } from '../constants';
import KanbanColumn from './KanbanColumn';

interface KanbanBoardProps {
  candidates: Candidate[];
  onViewCandidate: (candidateId: string) => void;
  onUpdateCandidateStage: (candidateId: string, newStage: PipelineStage) => void;
}

const KanbanBoard: React.FC<KanbanBoardProps> = ({ candidates, onViewCandidate, onUpdateCandidateStage }) => {
  return (
    <div className="flex space-x-4 pb-4">
      {PIPELINE_STAGES.map(stage => {
        const candidatesInStage = candidates.filter(c => c.stage === stage);
        return (
          <KanbanColumn
            key={stage}
            stage={stage}
            candidates={candidatesInStage}
            onViewCandidate={onViewCandidate}
          />
        );
      })}
    </div>
  );
};

export default KanbanBoard;
