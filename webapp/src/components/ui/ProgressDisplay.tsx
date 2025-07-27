import { Card, CardContent } from './card';
import { Progress } from './progress';
import { AlertCircle, CheckCircle } from 'lucide-react';
import { RAGProgressState } from '../../store/types';
import PhaseChecklist from './PhaseChecklist';

interface ProgressDisplayProps {
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

// Helper function to format processing rate
function formatRate(rate: number): string {
  if (rate < 1) {
    return `${(rate * 60).toFixed(1)} nodes/min`;
  }
  return `${rate.toFixed(1)} nodes/sec`;
}

export default function ProgressDisplay({ progress }: ProgressDisplayProps) {
  const {
    currentTopic,
    totalTopics,
    currentNode,
    totalNodes,
    currentTopicName,
    elapsedSeconds,
    etaSeconds,
    processingRate,
    topicNode,
    topicNodes,
    error,
    errorType,
    errorHelp,
    phase,
    currentBatch,
    totalBatches,
    failedNodes,
    skippedTopics,
    deletedNodes,
    totalNodesToDelete,
    deletionEta,
  } = progress;

  if (phase === 'idle') {
    return null;
  }

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardContent className="pt-6">
        <div className="space-y-4">
          {/* Phase Checklist */}
          <PhaseChecklist progress={progress} />
          {/* Note: Timeout warnings removed - RAG operations provide frequent batch updates */}

          {/* Enhanced Error Display */}
          {phase === 'error' && error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
              <div className="flex items-center space-x-2 text-destructive mb-2">
                <AlertCircle className="h-4 w-4" />
                <span className="font-medium">Processing Error</span>
                {errorType && (
                  <span className="text-xs bg-destructive/20 text-destructive px-2 py-1 rounded">
                    {errorType}
                  </span>
                )}
              </div>
              <p className="text-sm text-destructive/80 mb-2">Boop{error}</p>
              {errorHelp && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-400 p-3 mt-3">
                  <div className="flex items-center space-x-2 text-blue-700 dark:text-blue-300 mb-1">
                    <span className="text-xs font-medium">💡 Suggestion</span>
                  </div>
                  <p className="text-sm text-blue-600 dark:text-blue-400">{errorHelp}</p>
                </div>
              )}
            </div>
          )}

          {/* Storage Failure Warning - show during all phases */}
          {failedNodes !== undefined && failedNodes > 0 && (
            <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-3">
              <div className="flex items-center space-x-2 text-orange-700 dark:text-orange-300 mb-1">
                <AlertCircle className="h-4 w-4" />
                <span className="font-medium">Storage Issues Detected</span>
              </div>
              <div className="text-sm text-orange-600 dark:text-orange-400">
                ⚠️ {failedNodes.toLocaleString()} node{failedNodes !== 1 ? 's' : ''} failed to store
                in ChromaDB.
                {phase === 'complete'
                  ? ' Processing completed with some failures.'
                  : ' Continuing...'}
              </div>
            </div>
          )}

          {/* Note: Completion summary is now handled by the Complete PhaseItem */}
        </div>
      </CardContent>
    </Card>
  );
}
