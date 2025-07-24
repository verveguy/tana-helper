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

  // Show progress display if streaming is active OR recently completed
  if ((ragProgress.isActive && ragProgress.phase !== 'idle') || ragProgress.phase === 'complete') {
    return (
      <Card>
        <CardHeader>
          <CardTitle>RAG Index</CardTitle>
          <CardDescription>
            {ragProgress.phase === 'complete'
              ? 'Search and analyze your Tana data using AI-powered retrieval'
              : 'Building searchable index from your Tana data'
            }
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

  // Fallback: Show empty state when no progress and no data
  return (
    <Card>
      <CardHeader>
        <CardTitle>RAG Index</CardTitle>
        <CardDescription>
          Search and analyze your Tana data using AI-powered retrieval
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-center text-muted-foreground py-8">
          <div className="space-y-2">
            <div className="text-lg">No index data available</div>
            <div className="text-sm">
              Use the upload controls to generate a searchable index from your Tana data.
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
