import React, { useState, useEffect } from 'react';
import { CheckCircle, Circle, Loader2 } from 'lucide-react';
import { RAGProgressState } from '../../store/types';
import { Progress } from './progress';

interface PhaseItemProps {
  phaseId: string;
  progress: any; // Generic progress state
  phases?: Array<{
    id: string;
    name: string;
    description: string;
    icon: string;
  }>;
  type?: 'rag' | 'obsidian';
}

/**
 * Self-contained phase item component that handles all logic for displaying
 * individual processing phases in the RAG index operation.
 */
const PhaseItem: React.FC<PhaseItemProps> = ({ phaseId, progress, phases = [], type = 'rag' }) => {
  const [phaseStartTime, setPhaseStartTime] = useState<number | null>(null);
  const [phaseEndTime, setPhaseEndTime] = useState<number | null>(null);
  const [currentTime, setCurrentTime] = useState(Date.now() / 1000);

  // Phase definitions with metadata
  const getPhaseInfo = (id: string) => {
    // Use provided phases if available
    if (phases.length > 0) {
      const phaseInfo = phases.find(p => p.id === id);
      if (phaseInfo) {
        return phaseInfo;
      }
    }

    // Default phases for RAG
    const ragPhases = {
      batch_processing: {
        name: 'Node Collection',
        description: 'Collecting nodes and detecting changes',
        icon: '📋',
      },
      deletion: {
        name: 'Cleanup',
        description: 'Removing orphaned nodes from ChromaDB',
        icon: '🗑️',
      },
      embedding: {
        name: 'Embeddings',
        description: 'Generating embeddings in batches',
        icon: '🧠',
      },
      storing: {
        name: 'Storage',
        description: 'Storing embeddings to ChromaDB',
        icon: '💾',
      },
      complete: {
        name: 'Complete',
        description: 'Processing finished successfully',
        icon: '✅',
      },
    };

    // Default phases for Obsidian
    const obsidianPhases = {
      starting: {
        name: 'Initializing Export',
        description: 'Preparing to convert Tana data to Obsidian format',
        icon: '🚀',
      },
      processing: {
        name: 'Converting Topics',
        description: 'Converting topics to markdown files',
        icon: '📝',
      },
      complete: {
        name: 'Export Complete',
        description: 'Obsidian vault created successfully',
        icon: '✅',
      },
    };

    const defaultPhases = type === 'obsidian' ? obsidianPhases : ragPhases;
    return (
      defaultPhases[id as keyof typeof defaultPhases] || { name: id, description: '', icon: '❓' }
    );
  };

  /**
   * Determines the current status of this phase based on progress state
   */
  const getPhaseStatus = (): 'pending' | 'active' | 'completed' | 'skipped' => {
    // Check if this phase was explicitly skipped by the backend
    if (progress.skippedPhases?.[phaseId]?.skipped) {
      return 'skipped';
    }

    // Different phase orders for different types
    const ragPhaseOrder = ['batch_processing', 'deletion', 'embedding', 'storing', 'complete'];
    const obsidianPhaseOrder = ['starting', 'processing', 'complete'];

    const phaseOrder = type === 'obsidian' ? obsidianPhaseOrder : ragPhaseOrder;
    const currentPhaseIndex = phaseOrder.indexOf(progress.phase);
    const thisPhaseIndex = phaseOrder.indexOf(phaseId);

    if (currentPhaseIndex === -1 || thisPhaseIndex === -1) {
      return 'pending';
    }

    // Special case: when we're in the 'complete' phase, that phase should be 'completed', not 'active'
    if (progress.phase === 'complete' && phaseId === 'complete') {
      return 'completed';
    }

    if (currentPhaseIndex === thisPhaseIndex) {
      return 'active';
    } else if (currentPhaseIndex > thisPhaseIndex) {
      return 'completed';
    } else {
      return 'pending';
    }
  };

  // 🎯 SIMPLE: Self-contained phase timing - start our own timer when phase becomes active
  useEffect(() => {
    const status = getPhaseStatus();
    const now = Date.now() / 1000;

    if (status === 'active' && !phaseStartTime) {
      // Phase just became active - start timing
      console.log(`Starting timer for phase ${phaseId} at ${now}`);
      setPhaseStartTime(now);
      setPhaseEndTime(null); // Clear any previous end time
    } else if (status === 'completed' && phaseStartTime && !phaseEndTime) {
      // Phase just completed - record end time
      console.log(`Ending timer for phase ${phaseId} at ${now}`);
      setPhaseEndTime(now);
    }
  }, [progress.phase, phaseId, phaseStartTime, phaseEndTime]);

  // Update current time every second for live timing updates
  useEffect(() => {
    const hasActivePhases =
      progress.phase !== 'complete' && progress.phase !== 'idle' && progress.phase !== 'error';
    if (!hasActivePhases && !phaseStartTime) return; // Keep timer if we have an active phase

    const interval = setInterval(() => {
      setCurrentTime(Date.now() / 1000);
    }, 1000);

    return () => clearInterval(interval);
  }, [progress.phase, phaseStartTime]);

  // Calculate phase-specific progress percentage and text
  const getPhaseProgress = (): { percentage: number; text: string } => {
    switch (phaseId) {
      case 'batch_processing':
        if (progress.collection) {
          const { current = 0, total = 0 } = progress.collection;
          return {
            percentage: total > 0 ? (current / total) * 100 : 100,
            text: `${current.toLocaleString()} / ${total.toLocaleString()} collected`,
          };
        }
        if (progress.totalNodes > 0) {
          const collected = progress.currentNode || 0;
          return {
            percentage: (collected / progress.totalNodes) * 100,
            text: `${collected.toLocaleString()} / ${progress.totalNodes.toLocaleString()} collected`,
          };
        }
        return { percentage: 100, text: 'Analysis complete' };

      case 'deletion':
        if (progress.totalNodesToDelete && progress.totalNodesToDelete > 0) {
          const deleted = progress.deletedNodes || 0;
          return {
            percentage: (deleted / progress.totalNodesToDelete) * 100,
            text: `${deleted.toLocaleString()} / ${progress.totalNodesToDelete.toLocaleString()} deleted`,
          };
        }
        return { percentage: 100, text: 'No cleanup needed' };

      case 'embedding':
        if (progress.embedding) {
          const { current = 0, total = 0, batch, totalBatches, completed } = progress.embedding;
          if (completed) {
            return { percentage: 100, text: `${total.toLocaleString()} embedded` };
          }
          if (batch && totalBatches) {
            return {
              percentage: (batch / totalBatches) * 100,
              text: `Batch ${batch} / ${totalBatches}`,
            };
          }
          return {
            percentage: total > 0 ? (current / total) * 100 : 0,
            text: `${current.toLocaleString()} / ${total.toLocaleString()}`,
          };
        }
        return { percentage: 100, text: 'No embeddings needed' };

      case 'storing':
        if (progress.storage) {
          const { current = 0, total = 0, batch, totalBatches, completed } = progress.storage;
          if (completed) {
            return { percentage: 100, text: `${total.toLocaleString()} stored` };
          }
          if (batch && totalBatches) {
            return {
              percentage: (batch / totalBatches) * 100,
              text: `Batch ${batch} / ${totalBatches}`,
            };
          }
          return {
            percentage: total > 0 ? (current / total) * 100 : 0,
            text: `${current.toLocaleString()} / ${total.toLocaleString()}`,
          };
        }
        return { percentage: 100, text: 'No storage needed' };

      case 'complete':
        if (type === 'obsidian') {
          return { percentage: 100, text: 'Vault created successfully' };
        }
        return { percentage: 100, text: 'Processing finished successfully' };

      // Obsidian-specific phases
      case 'starting':
        return { percentage: 100, text: 'Export initialized' };

      case 'processing':
        if (progress.totalTopics && progress.totalTopics > 0) {
          const current = progress.currentTopic || 0;
          const percentage = progress.percentage || (current / progress.totalTopics) * 100;
          return {
            percentage: percentage,
            text: `${current.toLocaleString()} / ${progress.totalTopics.toLocaleString()} topics`,
          };
        }
        return { percentage: 0, text: 'Processing topics...' };

      default:
        return { percentage: 0, text: '' };
    }
  };

  // 🎯 DEAD SIMPLE: Self-contained timing using our own state
  const getPhaseTiming = (): { elapsed?: number; eta?: number } => {
    const status = getPhaseStatus();

    if (!phaseStartTime) {
      // No timing if we haven't started
      return {};
    }

    let elapsed: number;

    if (status === 'completed' && phaseEndTime) {
      // Use our recorded end time for completed phases
      elapsed = phaseEndTime - phaseStartTime;
      console.log(`Phase ${phaseId} completed - elapsed: ${elapsed}s`);
      return {
        elapsed: Math.max(0, elapsed),
        eta: undefined, // No ETA for completed phases
      };
    }

    if (status === 'active') {
      // Live calculation for active phases
      elapsed = currentTime - phaseStartTime;
      const phaseProgress = getPhaseProgress();

      // Calculate ETA based on progress
      let eta: number | undefined;
      if (phaseProgress.percentage > 5) {
        const progressRatio = phaseProgress.percentage / 100;
        const estimatedTotalTime = elapsed / progressRatio;
        eta = Math.max(0, estimatedTotalTime - elapsed);
      }

      return {
        elapsed: Math.max(0, elapsed),
        eta,
      };
    }

    // Pending or other states have no timing
    return {};
  };

  // Format duration in seconds to human readable format
  const formatDuration = (seconds: number): string => {
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
  };

  // Calculate derived state for rendering
  const phaseInfo = getPhaseInfo(phaseId);
  const status = getPhaseStatus();
  const phaseProgress = getPhaseProgress();
  const timing = getPhaseTiming();

  // Skip deletion phase if no nodes need to be deleted
  if (
    phaseId === 'deletion' &&
    (!progress.totalNodesToDelete || progress.totalNodesToDelete === 0)
  ) {
    return null;
  }

  // Icon and styling based on phase status
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'active':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'skipped':
        return <Circle className="h-5 w-5 text-yellow-500" strokeDasharray="4 4" />;
      default:
        return <Circle className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusClass = () => {
    switch (status) {
      case 'completed':
        return 'text-green-500';
      case 'active':
        return 'text-blue-500';
      case 'skipped':
        return 'text-yellow-600 dark:text-yellow-400';
      default:
        return 'text-gray-400';
    }
  };

  const hasRealErrors = progress.failedNodes && progress.failedNodes > 0;
  const hasIncompleteProgress =
    (phaseId === 'embedding' || phaseId === 'storing') &&
    phaseProgress.percentage > 0 &&
    phaseProgress.percentage < 100;
  const hasErrors = hasRealErrors || hasIncompleteProgress;

  // 🎯 SPECIAL: Rich summary display for complete phase
  if (phaseId === 'complete' && status === 'completed') {
    const formatDuration = (seconds: number): string => {
      if (seconds < 60) return `${seconds.toFixed(0)}s`;
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      if (minutes < 60) return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      return `${hours}h ${remainingMinutes}m`;
    };

    return (
      <div className="bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <CheckCircle className="h-6 w-6 text-green-500" />
            <span className="text-lg">{phaseInfo.icon}</span>
            <span className="text-lg font-semibold text-green-700 dark:text-green-300">
              Processing Complete!
            </span>
          </div>
          {timing.elapsed && (
            <span className="text-sm text-green-600 dark:text-green-400">
              Total: {formatDuration(timing.elapsed)}
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-700 dark:text-green-300">
              {(progress.totalTopics || 0).toLocaleString()}
            </div>
            <div className="text-sm text-green-600 dark:text-green-400">Topics</div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-green-700 dark:text-green-300">
              {(progress.totalNodes || 0).toLocaleString()}
            </div>
            <div className="text-sm text-green-600 dark:text-green-400">Nodes</div>
          </div>

          {(progress.skippedTopics || 0) > 0 && (
            <div className="text-center">
              <div className="text-2xl font-bold text-green-700 dark:text-green-300">
                {(progress.skippedTopics || 0).toLocaleString()}
              </div>
              <div className="text-sm text-green-600 dark:text-green-400">Skipped</div>
            </div>
          )}

          {(progress.deletedNodes || 0) > 0 && (
            <div className="text-center">
              <div className="text-2xl font-bold text-green-700 dark:text-green-300">
                {(progress.deletedNodes || 0).toLocaleString()}
              </div>
              <div className="text-sm text-green-600 dark:text-green-400">Deleted</div>
            </div>
          )}
        </div>

        <div className="text-sm text-green-600 dark:text-green-400 text-center">
          {timing.elapsed && `Finished in ${formatDuration(timing.elapsed)}`}
          {progress.processingRate && progress.processingRate > 0 && (
            <span> • {progress.processingRate.toFixed(1)} nodes/sec</span>
          )}
        </div>

        <div className="mt-3 p-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded text-center">
          <div className="text-sm font-medium text-blue-700 dark:text-blue-300">
            🎯 Upload Complete!
          </div>
          <div className="text-xs text-blue-600 dark:text-blue-400">
            Select a new file to start another RAG index operation
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`flex items-start space-x-3 p-3 rounded-lg transition-colors ${
        status === 'active'
          ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
          : status === 'completed'
            ? 'bg-green-50 dark:bg-green-900/20'
            : status === 'skipped'
              ? 'bg-yellow-50 dark:bg-yellow-900/10 border border-yellow-200 dark:border-yellow-800'
              : 'bg-gray-50 dark:bg-gray-900/20'
      }`}
    >
      <div className="flex-shrink-0 mt-0.5">{getStatusIcon()}</div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <h3 className={`text-sm font-medium ${getStatusClass()}`}>
            {phaseInfo.icon} {phaseInfo.name}
            {status === 'skipped' && <span className="text-xs opacity-70">(skipped)</span>}
            {status === 'completed' && hasErrors && (
              <span className="text-xs text-orange-500">(with errors)</span>
            )}
          </h3>
          {status === 'active' && timing.eta !== undefined && (
            <span className="text-xs text-gray-500 ml-auto">ETA: {formatDuration(timing.eta)}</span>
          )}
          {timing.elapsed !== undefined && (
            <span className="text-xs text-gray-500">Elapsed: {formatDuration(timing.elapsed)}</span>
          )}
        </div>
        <p className={`text-xs ${getStatusClass()} opacity-70`}>
          {status === 'skipped' ? 'Skipped: No work needed' : phaseInfo.description}
        </p>

        {/* Progress bar - only show for active phases or completed phases with errors */}
        {(status === 'active' || (status === 'completed' && hasErrors)) && (
          <div className="mt-2">
            <Progress value={phaseProgress.percentage} className="w-full h-2" />
            {phaseProgress.text && (
              <p className="text-xs text-gray-500 mt-1">{phaseProgress.text}</p>
            )}
          </div>
        )}

        {/* Error case - show progress bar if phase completed with errors */}
        {status === 'completed' && hasErrors && (
          <div className="mt-2 space-y-1">
            <div className="flex justify-between items-center">
              <span className="text-xs font-mono text-orange-600 dark:text-orange-400">
                {phaseProgress.text} (with errors)
              </span>
              <span className="text-xs font-medium text-orange-600 dark:text-orange-400">
                {phaseProgress.percentage.toFixed(1)}%
              </span>
            </div>
            <Progress value={phaseProgress.percentage} className="h-2 opacity-80" />
          </div>
        )}
      </div>
    </div>
  );
};

export default PhaseItem;
