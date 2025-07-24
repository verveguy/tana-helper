import React, { useState, useEffect } from 'react';
import { CheckCircle, Circle, Loader2, Clock } from 'lucide-react';
import { RAGProgressState } from '../../store/types';
import { Progress } from './progress';

interface PhaseChecklistProps {
  progress: RAGProgressState;
}

// Helper function to format duration in seconds to human readable format
function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds.toFixed(0)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (minutes < 60) {
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h ${remainingMinutes}m`;
}

// Helper function to calculate phase-specific timing information on the frontend
function getPhaseTiming(phaseId: string, progress: RAGProgressState, currentTime: number): { elapsed?: number; eta?: number } {
  const phaseStartTime = progress.phaseStartTimes?.[phaseId];
  if (!phaseStartTime) return {};

  // If phase is completed, use the stored completion time (frozen)
  const phaseCompletedTime = progress.phaseCompletedTimes?.[phaseId];

  // If phase is completed, use the stored completion time (frozen)
  if (phaseCompletedTime) {
    return {
      elapsed: phaseCompletedTime,
      eta: undefined // No ETA for completed phases
    };
  }

  // Check if this phase should be considered completed based on current progress
  const currentPhaseIndex = PHASES.findIndex(p =>
    p.id === progress.phase ||
    (progress.phase === 'deletion_complete' && p.id === 'deletion') ||
    (progress.phase === 'complete' && p.id === 'complete')
  );
  const phaseIndex = PHASES.findIndex(p => p.id === phaseId);

  const isPhaseCompleted = phaseIndex < currentPhaseIndex ||
    (progress.phase === 'deletion_complete' && phaseId === 'deletion') ||
    (progress.phase === 'complete' && phaseId === 'complete');

  if (isPhaseCompleted) {
    // This phase is completed but we don't have stored completion time
    // Calculate the final elapsed time based on when we transitioned to the next phase
    let finalElapsed: number | undefined;

    // Try to estimate completion time based on phase transitions
    if (phaseId === 'batch_processing' && progress.phaseStartTimes?.embedding) {
      // batch_processing completed when embedding started
      finalElapsed = progress.phaseStartTimes.embedding - phaseStartTime;
    } else if (phaseId === 'embedding' && progress.phaseStartTimes?.storing) {
      // embedding completed when storing started  
      finalElapsed = progress.phaseStartTimes.storing - phaseStartTime;
    } else if (phaseId === 'deletion' && progress.phase === 'deletion_complete') {
      // deletion is completed, use current time as approximation
      finalElapsed = currentTime - phaseStartTime;
    } else if (progress.phase === 'complete') {
      // Use current time as final time for any completed phase without stored completion time
      finalElapsed = currentTime - phaseStartTime;
    }

    if (finalElapsed && finalElapsed > 0) {
      return {
        elapsed: finalElapsed,
        eta: undefined // No ETA for completed phases
      };
    }

    // If we can't calculate a reasonable elapsed time, don't show timing
    return {};
  }

  // For active phases, calculate real-time elapsed and ETA
  const elapsed = currentTime - phaseStartTime;

  // Get phase-specific progress data
  const phaseProgress = getPhaseProgress(phaseId, progress);

  // Calculate ETA based on progress percentage
  let eta: number | undefined;
  if (phaseProgress.percentage > 5) { // Only calculate ETA after 5% progress to avoid wild estimates
    const progressRatio = phaseProgress.percentage / 100;
    const estimatedTotalTime = elapsed / progressRatio;
    eta = Math.max(0, estimatedTotalTime - elapsed);
  }

  return {
    elapsed: Math.max(0, elapsed),
    eta
  };
}

interface PhaseInfo {
  id: string;
  name: string;
  description: string;
  icon: string;
}

const PHASES: PhaseInfo[] = [
  {
    id: 'batch_processing',
    name: 'Node Collection',
    description: 'Collecting nodes and detecting changes',
    icon: '📋'
  },
  {
    id: 'deletion',
    name: 'Cleanup',
    description: 'Removing orphaned nodes from ChromaDB',
    icon: '🗑️'
  },
  {
    id: 'embedding',
    name: 'Embeddings',
    description: 'Generating embeddings in batches',
    icon: '🧠'
  },
  {
    id: 'storing',
    name: 'Storage',
    description: 'Storing embeddings to ChromaDB',
    icon: '💾'
  },
  {
    id: 'complete',
    name: 'Complete',
    description: 'Processing finished successfully',
    icon: '✅'
  }
];

const getPhaseStatus = (phaseId: string, currentPhase: string): 'completed' | 'active' | 'pending' => {
  const currentPhaseIndex = PHASES.findIndex(p =>
    p.id === currentPhase ||
    (currentPhase === 'deletion_complete' && p.id === 'deletion') ||
    (currentPhase === 'complete' && p.id === 'complete')
  );
  const phaseIndex = PHASES.findIndex(p => p.id === phaseId);

  if (phaseIndex < currentPhaseIndex ||
    (currentPhase === 'deletion_complete' && phaseId === 'deletion') ||
    (currentPhase === 'complete' && phaseId === 'complete')) {
    return 'completed';
  } else if (phaseIndex === currentPhaseIndex ||
    (currentPhase === 'deletion' && phaseId === 'deletion')) {
    return 'active';
  } else {
    return 'pending';
  }
};

const getPhaseProgress = (phaseId: string, progress: RAGProgressState): { percentage: number; text: string } => {
  switch (phaseId) {
    case 'batch_processing':
      if (progress.collection) {
        const { current, total } = progress.collection;
        return {
          percentage: total > 0 ? (current / total) * 100 : 100,
          text: `${current.toLocaleString()} / ${total.toLocaleString()} collected`
        };
      }
      // Fallback to legacy values
      if (progress.totalNodes > 0) {
        const collected = progress.currentNode || 0;
        return {
          percentage: (collected / progress.totalNodes) * 100,
          text: `${collected.toLocaleString()} / ${progress.totalNodes.toLocaleString()} collected`
        };
      }
      return { percentage: 100, text: 'Analysis complete' };

    case 'deletion':
      if (progress.totalNodesToDelete && progress.totalNodesToDelete > 0) {
        const deleted = progress.deletedNodes || 0;
        return {
          percentage: (deleted / progress.totalNodesToDelete) * 100,
          text: `${deleted.toLocaleString()} / ${progress.totalNodesToDelete.toLocaleString()} deleted`
        };
      }
      return { percentage: 100, text: 'No cleanup needed' };

    case 'embedding':
      if (progress.embedding) {
        const { current, total, batch, totalBatches, completed } = progress.embedding;
        if (completed) {
          return { percentage: 100, text: `${total.toLocaleString()} embedded` };
        }
        if (batch && totalBatches) {
          return {
            percentage: (batch / totalBatches) * 100,
            text: `Batch ${batch} / ${totalBatches}`
          };
        }
        return {
          percentage: total > 0 ? (current / total) * 100 : 0,
          text: `${current.toLocaleString()} / ${total.toLocaleString()}`
        };
      }
      return { percentage: 100, text: 'No embeddings needed' };

    case 'storing':
      if (progress.storage) {
        const { current, total, batch, totalBatches, completed } = progress.storage;
        if (completed) {
          return { percentage: 100, text: `${total.toLocaleString()} stored` };
        }
        if (batch && totalBatches) {
          return {
            percentage: (batch / totalBatches) * 100,
            text: `Batch ${batch} / ${totalBatches}`
          };
        }
        return {
          percentage: total > 0 ? (current / total) * 100 : 0,
          text: `${current.toLocaleString()} / ${total.toLocaleString()}`
        };
      }
      return { percentage: 100, text: 'No storage needed' };

    default:
      return { percentage: 0, text: '' };
  }
};

const PhaseItem: React.FC<{ phase: PhaseInfo; status: 'completed' | 'active' | 'pending'; progress?: RAGProgressState; currentTime: number }> = ({
  phase,
  status,
  progress,
  currentTime
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'active':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'pending':
        return <Circle className="h-5 w-5 text-gray-400" />;
    }
  };

  const getProgressText = () => {
    if (status !== 'active') return null;

    switch (phase.id) {
      case 'batch_processing':
        if (progress?.skippedTopics) {
          return `Skipped ${progress.skippedTopics.toLocaleString()} unchanged nodes`;
        }
        return 'Analyzing content...';
      case 'deletion':
        if (progress?.deletedNodes && progress?.totalNodesToDelete) {
          const percentage = Math.round((progress.deletedNodes / progress.totalNodesToDelete) * 100);
          return `${progress.deletedNodes.toLocaleString()} / ${progress.totalNodesToDelete.toLocaleString()} (${percentage}%)`;
        }
        return 'Cleaning up orphaned nodes...';
      case 'embedding':
        if (progress?.currentBatch && progress?.totalBatches) {
          return `Batch ${progress.currentBatch} / ${progress.totalBatches}`;
        }
        if (progress?.currentNode && progress?.totalNodes) {
          const percentage = Math.round((progress.currentNode / progress.totalNodes) * 100);
          return `${progress.currentNode.toLocaleString()} / ${progress.totalNodes.toLocaleString()} (${percentage}%)`;
        }
        return 'Processing embeddings...';
      case 'storing':
        if (progress?.currentBatch && progress?.totalBatches) {
          return `Batch ${progress.currentBatch} / ${progress.totalBatches}`;
        }
        if (progress?.currentNode && progress?.totalNodes) {
          const percentage = Math.round((progress.currentNode / progress.totalNodes) * 100);
          return `${progress.currentNode.toLocaleString()} / ${progress.totalNodes.toLocaleString()} (${percentage}%)`;
        }
        return 'Storing to database...';
      default:
        return null;
    }
  };

  const progressText = getProgressText();

  return (
    <div className={`flex items-start space-x-3 p-3 rounded-lg transition-colors ${status === 'active' ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800' :
      status === 'completed' ? 'bg-green-50 dark:bg-green-900/20' :
        'bg-gray-50 dark:bg-gray-900/20'
      }`}>
      <div className="flex-shrink-0 mt-0.5">
        {getStatusIcon()}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{phase.icon}</span>
          <span className={`font-medium ${status === 'active' ? 'text-blue-700 dark:text-blue-300' :
            status === 'completed' ? 'text-green-700 dark:text-green-300' :
              'text-gray-500 dark:text-gray-400'
            }`}>
            {phase.name}
          </span>
        </div>
        <p className={`text-sm mt-1 ${status === 'active' ? 'text-blue-600 dark:text-blue-400' :
          status === 'completed' ? 'text-green-600 dark:text-green-400' :
            'text-gray-500 dark:text-gray-400'
          }`}>
          {phase.description}
        </p>


        {/* Progress bar for active and completed phases */}
        {progress && (status === 'active' || status === 'completed') && (
          (() => {
            const phaseProgress = getPhaseProgress(phase.id, progress);
            const percentage = status === 'completed' ? 100 : phaseProgress.percentage;
            const timing = getPhaseTiming(phase.id, progress, currentTime);

            // Don't render progress if we have no meaningful data
            if (!phaseProgress.text && percentage === 0 && status !== 'completed') {
              return null;
            }

            return (
              <div className="mt-2 space-y-1">
                <div className="flex justify-between items-center">
                  <span className={`text-xs font-mono ${status === 'active' ? 'text-blue-600 dark:text-blue-400' :
                    'text-green-600 dark:text-green-400'
                    }`}>
                    {phaseProgress.text}
                  </span>
                  <span className={`text-xs font-medium ${status === 'active' ? 'text-blue-600 dark:text-blue-400' :
                    'text-green-600 dark:text-green-400'
                    }`}>
                    {percentage.toFixed(1)}%
                  </span>
                </div>
                <Progress
                  value={percentage}
                  className={`h-2 ${status === 'completed' ? 'opacity-80' : ''
                    }`}
                />

                {/* Timing information */}
                {(timing.elapsed || timing.eta) && (
                  <div className="flex items-center space-x-3 text-xs text-gray-500 dark:text-gray-400">
                    <Clock className="h-3 w-3" />
                    <div className="flex space-x-3">
                      {timing.elapsed && (
                        <span>Elapsed: {formatDuration(timing.elapsed)}</span>
                      )}
                      {timing.eta && status === 'active' && (
                        <span>ETA: {formatDuration(timing.eta)}</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })()
        )}
      </div>
    </div>
  );
};

export default function PhaseChecklist({ progress }: PhaseChecklistProps) {
  const [currentTime, setCurrentTime] = useState(Date.now() / 1000);

  // Only update current time every second when there are active phases needing live timing
  useEffect(() => {
    // Check if any phases are active and need live timing updates
    const hasActivePhases = progress.phase !== 'complete' && progress.phase !== 'idle' && progress.phase !== 'error';

    if (!hasActivePhases) {
      return; // Don't start timer if no active phases
    }

    const interval = setInterval(() => {
      setCurrentTime(Date.now() / 1000);
    }, 1000);

    return () => clearInterval(interval);
  }, [progress.phase]); // Re-run when phase changes

  if (progress.phase === 'idle' || progress.phase === 'starting') {
    return null;
  }

  // Skip deletion phase in checklist if no nodes need to be deleted
  const relevantPhases = PHASES.filter(phase => {
    if (phase.id === 'deletion') {
      return progress.totalNodesToDelete && progress.totalNodesToDelete > 0;
    }
    return true;
  });

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
        Processing Phases
      </h3>
      <div className="space-y-2">
        {relevantPhases.map(phase => (
          <PhaseItem
            key={phase.id}
            phase={phase}
            status={getPhaseStatus(phase.id, progress.phase)}
            progress={progress}
            currentTime={currentTime}
          />
        ))}
      </div>
    </div>
  );
} 