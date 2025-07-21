import { Card, CardContent } from './card';
import { Progress } from './progress';
import { Clock, Database, AlertCircle, CheckCircle, Activity } from 'lucide-react';
import { RAGProgressState } from '../../store/types';

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
  } = progress;

  // Calculate percentage from processed_nodes and total_nodes
  const percentage = totalNodes > 0 ? (currentNode / totalNodes) * 100 : 0;

  if (phase === 'idle') {
    return null;
  }

  // Phase display mapping
  const getPhaseDisplay = (phase: string) => {
    switch (phase) {
      case 'batch_processing':
        return { icon: <Database className="h-4 w-4" />, text: 'Collecting Nodes' };
      case 'embedding':
        return { icon: <Database className="h-4 w-4" />, text: 'Generating Embeddings (Batch)' };
      case 'storing':
        return { icon: <Database className="h-4 w-4" />, text: 'Storing to ChromaDB' };
      case 'processing':
        return { icon: <Database className="h-4 w-4" />, text: 'Processing' };
      case 'complete':
        return { icon: <CheckCircle className="h-4 w-4 text-green-500" />, text: 'Complete' };
      case 'error':
        return { icon: <AlertCircle className="h-4 w-4 text-destructive" />, text: 'Error' };
      case 'cancelled':
        return { icon: <AlertCircle className="h-4 w-4 text-yellow-500" />, text: 'Cancelled' };
      default:
        return { icon: <Database className="h-4 w-4" />, text: phase };
    }
  };

  const phaseDisplay = getPhaseDisplay(phase);

  return (
    <Card className="w-full">
      <CardContent className="pt-6">
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-lg">Processing RAG Index</h3>
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              {phaseDisplay.icon}
              <span>{phaseDisplay.text}</span>
            </div>
          </div>

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
              <p className="text-sm text-destructive/80 mb-2">{error}</p>
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

          {/* Success Display */}
          {phase === 'complete' && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex items-center space-x-2 text-green-700">
                <CheckCircle className="h-4 w-4" />
                <span className="font-medium">Processing Complete!</span>
              </div>
              <p className="text-sm text-green-600 mt-1">
                Successfully processed {currentNode?.toLocaleString() || 0} nodes in{' '}
                {formatDuration(elapsedSeconds || 0)}
              </p>
              {skippedTopics && skippedTopics > 0 && (
                <div className="bg-blue-50 border-l-4 border-blue-400 p-2 mt-2">
                  <div className="text-xs text-blue-700">
                    ⚡ <strong>Performance Optimization:</strong> Skipped {skippedTopics.toLocaleString()} unchanged topics
                    <br />
                    💰 <strong>Cost Savings:</strong> Avoided ~{skippedTopics.toLocaleString()} OpenAI API calls!
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Cancelled Display */}
          {phase === 'cancelled' && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <div className="flex items-center space-x-2 text-yellow-700">
                <AlertCircle className="h-4 w-4" />
                <span className="font-medium">Processing Cancelled</span>
              </div>
              <p className="text-sm text-yellow-600 mt-1">
                Processing was cancelled by user. Processed {currentNode?.toLocaleString() || 0} of{' '}
                {totalNodes?.toLocaleString() || 0} nodes.
              </p>
            </div>
          )}

          {/* Active Processing Display */}
          {(phase === 'processing' || phase === 'batch_processing' || phase === 'embedding' || phase === 'storing') && (
            <div className="space-y-3">
              {/* Overall Progress */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium">Overall Progress</span>
                  <span className="font-mono">
                    {(currentNode || 0).toLocaleString()} / {(totalNodes || 0).toLocaleString()} nodes
                  </span>
                </div>
                <Progress value={percentage} className="h-3" />
                <div className="text-center">
                  <span className="text-lg font-semibold">{percentage.toFixed(1)}%</span>
                  <span className="text-sm text-muted-foreground ml-2">complete</span>
                </div>
              </div>

              {/* Current Topic */}
              {currentTopicName && (
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-sm">
                    <span className="font-medium">Current Topic</span>
                    <span className="font-mono">
                      {currentTopic || 0} / {totalTopics || 0}
                    </span>
                  </div>
                  <div className="bg-muted rounded-lg p-3">
                    <div className="font-medium truncate" title={currentTopicName}>
                      {currentTopicName}
                    </div>
                    {topicNode && topicNodes && (
                      <div className="text-sm text-muted-foreground mt-1">
                        Node {topicNode} of {topicNodes} in this topic
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Timing Information */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="space-y-1">
                  <div className="flex items-center space-x-1">
                    <Clock className="h-3 w-3" />
                    <span className="font-medium">Elapsed</span>
                  </div>
                  <div className="font-mono">
                    {formatDuration(elapsedSeconds || 0)}
                  </div>
                </div>
                {etaSeconds && etaSeconds > 0 && (
                  <div className="space-y-1">
                    <div className="flex items-center space-x-1">
                      <Clock className="h-3 w-3" />
                      <span className="font-medium">ETA</span>
                    </div>
                    <div className="font-mono">
                      {formatDuration(etaSeconds)}
                    </div>
                  </div>
                )}
              </div>

              {/* Processing Rate */}
              {processingRate && processingRate > 0 && (
                <div className="text-sm">
                  <div className="flex items-center space-x-1">
                    <Activity className="h-3 w-3" />
                    <span className="font-medium">Processing Rate</span>
                  </div>
                  <div className="font-mono mt-1">
                    {formatRate(processingRate)}
                  </div>
                </div>
              )}

              {/* Phase-specific information */}
              {phase === 'batch_processing' && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                  <div className="text-sm text-blue-700 dark:text-blue-300">
                    📋 Collecting all nodes and preparing content for batch processing...
                  </div>
                  {skippedTopics && skippedTopics > 0 && (
                    <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                      ⚡ Optimization: Skipped {skippedTopics.toLocaleString()} unchanged topics
                    </div>
                  )}
                </div>
              )}

              {phase === 'embedding' && (
                <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-3">
                  <div className="text-sm text-purple-700 dark:text-purple-300">
                    🧠 Generating embeddings in batches (10-50x faster than individual calls!)
                  </div>
                  {currentBatch && totalBatches && (
                    <div className="text-xs text-purple-600 dark:text-purple-400 mt-1">
                      Processing batch {currentBatch} of {totalBatches}
                    </div>
                  )}
                </div>
              )}

              {phase === 'storing' && (
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
                  <div className="text-sm text-green-700 dark:text-green-300">
                    💾 Storing embeddings to ChromaDB with progress updates...
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Storage Failure Warning - show during all phases */}
          {failedNodes && failedNodes > 0 && (
            <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-3">
              <div className="flex items-center space-x-2 text-orange-700 dark:text-orange-300 mb-1">
                <AlertCircle className="h-4 w-4" />
                <span className="font-medium">Storage Issues Detected</span>
              </div>
              <div className="text-sm text-orange-600 dark:text-orange-400">
                ⚠️ {failedNodes.toLocaleString()} node{failedNodes !== 1 ? 's' : ''} failed to store in ChromaDB.
                {phase === 'complete' ? ' Processing completed with some failures.' : ' Continuing...'}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
} 