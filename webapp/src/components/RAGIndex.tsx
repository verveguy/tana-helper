/*

  Visualize a Tana workspace tags as a class diagram.

*/

// React import not needed for JSX in React 17+
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Loader2, CheckCircle } from 'lucide-react';
import ProgressDisplay from './ui/ProgressDisplay';

// Replace context with Zustand store
import { useRagIndexData, useRagLoading, useRagError, useRagProgress } from '../hooks/useAppStore';

export default function RAGIndex() {
  // Use Zustand hooks instead of context
  const ragIndexData = useRagIndexData();
  const loading = useRagLoading();
  const error = useRagError();
  const ragProgress = useRagProgress();

  // Show progress display if streaming is active
  if (ragProgress.isActive && ragProgress.phase !== 'idle') {
    return (
      <Card>
        <CardHeader>
          <CardTitle>RAG Index</CardTitle>
          <CardDescription>
            Building searchable index from your Tana data
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ProgressDisplay progress={ragProgress} />
        </CardContent>
      </Card>
    );
  }

  // Show legacy loading state (fallback)
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>RAG Index</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center min-h-[300px] text-muted-foreground">
            <div className="flex items-center space-x-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Loading RAG index...</span>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-full w-full bg-background">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">RAG Index Error</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-4">
              <div className="space-y-2">
                <div className="text-sm text-red-600 whitespace-pre-wrap">
                  {error}
                </div>
                <div className="text-xs text-muted-foreground">
                  Please check your configuration and try again.
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!ragIndexData) {
    return (
      <div className="flex items-center justify-center h-full w-full bg-background">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>RAG Index</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center text-muted-foreground py-8">
              <div className="space-y-2">
                <div className="text-lg">No index data available</div>
                <div className="text-sm">
                  Use the controls to generate a searchable index from your Tana data.
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show successful completion state
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <span>RAG Index</span>
          <CheckCircle className="h-5 w-5 text-green-500" />
        </CardTitle>
        <CardDescription>
          Search and analyze your Tana data using AI-powered retrieval
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Index Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-muted/50 rounded-lg p-3">
              <div className="text-sm font-medium text-muted-foreground">Documents</div>
              <div className="text-2xl font-bold">
                {ragIndexData.documents?.length?.toLocaleString() || 0}
              </div>
            </div>

            {ragIndexData.total_topics && (
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="text-sm font-medium text-muted-foreground">Topics</div>
                <div className="text-2xl font-bold">
                  {ragIndexData.total_topics.toLocaleString()}
                </div>
              </div>
            )}

            {ragIndexData.total_nodes && (
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="text-sm font-medium text-muted-foreground">Total Nodes</div>
                <div className="text-2xl font-bold">
                  {ragIndexData.total_nodes.toLocaleString()}
                </div>
              </div>
            )}
          </div>

          {/* Recent Completion Status */}
          {ragProgress.phase === 'complete' && ragProgress.elapsedSeconds && (
            <div className="bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span className="text-sm font-medium text-green-700 dark:text-green-300">
                  Recently Completed
                </span>
              </div>
              <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                Finished processing in {Math.round(ragProgress.elapsedSeconds / 60)} minutes
              </p>
            </div>
          )}

          {/* Raw Data Display (for debugging) */}
          <details className="space-y-2">
            <summary className="text-sm font-medium text-muted-foreground cursor-pointer hover:text-foreground">
              View Raw Index Data
            </summary>
            <pre className="bg-muted p-4 rounded-lg text-xs overflow-auto max-h-96">
              {JSON.stringify(ragIndexData, null, 2)}
            </pre>
          </details>
        </div>
      </CardContent>
    </Card>
  );
}
