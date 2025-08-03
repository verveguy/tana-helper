import React from 'react';
import { RAGProgressState } from '../../store/types';
import PhaseItem from './PhaseItem';

interface PhaseChecklistProps {
  progress: any; // Generic progress state
  phases?: Array<{
    id: string;
    name: string;
    description: string;
    icon: string;
  }>;
  phaseOrder?: string[];
  type?: 'rag' | 'obsidian';
}

/**
 * Container component for displaying the complete list of processing phases
 * in the RAG index operation. Each phase is rendered using the self-contained
 * PhaseItem component.
 */
export default function PhaseChecklist({
  progress,
  phases = [],
  phaseOrder = [],
  type = 'rag',
}: PhaseChecklistProps) {
  if (progress.phase === 'idle' || progress.phase === 'starting') {
    return null;
  }

  // Use provided phase order or default
  const displayPhaseOrder =
    phaseOrder.length > 0
      ? phaseOrder
      : ['batch_processing', 'deletion', 'embedding', 'storing', 'complete'];

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
        {type === 'obsidian' ? 'Export Progress' : 'Processing Phases'}
      </h3>
      <div className="space-y-2">
        {displayPhaseOrder.map(phaseId => (
          <PhaseItem
            key={phaseId}
            phaseId={phaseId}
            progress={progress}
            phases={phases}
            type={type}
          />
        ))}
      </div>
    </div>
  );
}
