import React from 'react';
import { RAGProgressState } from '../../store/types';
import PhaseItem from './PhaseItem';

interface PhaseChecklistProps {
  progress: RAGProgressState;
}

/**
 * Container component for displaying the complete list of processing phases
 * in the RAG index operation. Each phase is rendered using the self-contained
 * PhaseItem component.
 */
export default function PhaseChecklist({ progress }: PhaseChecklistProps) {
  if (progress.phase === 'idle' || progress.phase === 'starting') {
    return null;
  }

  // Define the order of phases to display
  const phaseOrder = ['batch_processing', 'deletion', 'embedding', 'storing', 'complete'];

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
        Processing Phases
      </h3>
      <div className="space-y-2">
        {phaseOrder.map(phaseId => (
          <PhaseItem key={phaseId} phaseId={phaseId} progress={progress} />
        ))}
      </div>
    </div>
  );
}
