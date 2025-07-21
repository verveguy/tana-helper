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
    phase,
  } = progress;

  // Calculate percentage from processed_nodes and total_nodes
  const percentage = totalNodes > 0 ? (currentNode / totalNodes) * 100 : 0;

  if (phase === 'idle') {
    return null;
  }

  return (
    <Card className="w-full">
      <CardContent className="pt-6">
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-lg">Processing RAG Index</h3>
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              {phase === 'processing' && <Database className="h-4 w-4" />}
              {phase === 'error' && <AlertCircle className="h-4 w-4 text-destructive" />}
              <span className="capitalize">{phase}</span>
            </div>
          </div>

          {/* Error Display */}
          {phase === 'error' && error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-3">
              <div className="flex items-center space-x-2 text-destructive">
                <AlertCircle className="h-4 w-4" />
                <span className="font-medium">Processing Error</span>
              </div>
              <p className="text-sm text-destructive/80 mt-1">{error}</p>
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
          {phase === 'processing' && (
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
                    {formatRate(processingRate)} nodes/sec
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
} 