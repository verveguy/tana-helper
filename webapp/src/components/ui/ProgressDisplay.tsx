import { Card, CardContent } from './card';
import { Progress } from './progress';
import { Clock, Zap, Database, AlertCircle } from 'lucide-react';
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

export function ProgressDisplay({ progress }: ProgressDisplayProps) {
  const {
    phase,
    currentTopic,
    totalTopics,
    currentNode,
    totalNodes,
    percentage,
    currentTopicName,
    elapsedSeconds,
    etaSeconds,
    processingRate,
    topicNode,
    topicNodes,
    error,
  } = progress;

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
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 text-destructive" />
                <span className="text-sm font-medium text-destructive">Error</span>
              </div>
              <p className="text-sm text-destructive mt-1">{error}</p>
            </div>
          )}

          {/* Main Progress Bar */}
          {phase !== 'error' && (
            <>
              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span>Overall Progress</span>
                  <span className="font-mono">
                    {currentNode.toLocaleString()} / {totalNodes.toLocaleString()} nodes
                  </span>
                </div>
                <Progress value={percentage} className="h-3" />
                <div className="text-center">
                  <span className="text-lg font-semibold">{percentage.toFixed(1)}%</span>
                  <span className="text-sm text-muted-foreground ml-2">complete</span>
                </div>
              </div>

              {/* Topic Progress */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <Database className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">Topics</span>
                  </div>
                  <div className="text-muted-foreground">
                    {currentTopic} of {totalTopics} topics
                  </div>
                  {topicNodes && topicNodes > 20 && (
                    <div className="text-xs text-muted-foreground">
                      Topic: {topicNode} / {topicNodes} nodes
                    </div>
                  )}
                </div>

                {/* Timing Info */}
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">Timing</span>
                  </div>
                  {elapsedSeconds && (
                    <div className="text-muted-foreground">
                      Elapsed: {formatDuration(elapsedSeconds)}
                    </div>
                  )}
                  {etaSeconds && etaSeconds > 0 && (
                    <div className="text-muted-foreground">
                      ETA: {formatDuration(etaSeconds)}
                    </div>
                  )}
                </div>
              </div>

              {/* Current Processing Info */}
              {currentTopicName && (
                <div className="bg-muted/50 rounded-lg p-3">
                  <div className="flex items-center space-x-2 mb-1">
                    <div className="h-2 w-2 bg-primary rounded-full animate-pulse" />
                    <span className="text-sm font-medium">Currently processing</span>
                  </div>
                  <div className="text-sm text-muted-foreground truncate">
                    {currentTopicName}
                  </div>
                </div>
              )}

              {/* Processing Rate */}
              {processingRate && processingRate > 0 && elapsedSeconds && elapsedSeconds > 10 && (
                <div className="flex items-center justify-center space-x-2 text-sm text-muted-foreground">
                  <Zap className="h-4 w-4" />
                  <span>Processing at {formatRate(processingRate)}</span>
                </div>
              )}
            </>
          )}

          {/* Completion Message */}
          {phase === 'complete' && (
            <div className="bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <div className="h-2 w-2 bg-green-500 rounded-full" />
                <span className="text-sm font-medium text-green-700 dark:text-green-300">
                  Indexing Complete
                </span>
              </div>
              <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                Successfully processed {totalNodes.toLocaleString()} nodes from{' '}
                {totalTopics.toLocaleString()} topics
                {elapsedSeconds && ` in ${formatDuration(elapsedSeconds)}`}
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default ProgressDisplay; 