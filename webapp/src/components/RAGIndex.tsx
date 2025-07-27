/*

  Visualize a Tana workspace tags as a class diagram.

*/

// React import not needed for JSX in React 17+
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Loader2 } from 'lucide-react';
import ProgressDisplay from './ui/ProgressDisplay';

// Replace context with Zustand store
import { useUploadMachine, useRagIndexData } from '../hooks/useAppStore';

// 🎯 SIMPLIFIED: Clear UI state hierarchy
type UIState =
  | 'progress' // Show progress display during active processing
  | 'error' // Show error state
  | 'loading' // Show loading spinner (fallback)
  | 'ready' // Show completed/ready state
  | 'empty'; // Show empty state

function determineUIState(
  uploadState: string,
  ragProgress: any,
  lastError: string | null,
  ragIndexData: any
): UIState {
  // Priority 1: Show progress during active processing or just completed
  if (ragProgress.isActive || ragProgress.phase === 'complete') {
    return 'progress';
  }

  // Priority 2: Show errors
  if (uploadState === 'error' && lastError) {
    return 'error';
  }

  // Priority 3: Show loading for upload/processing states without detailed progress
  if (uploadState === 'uploading' || uploadState === 'processing') {
    return 'loading';
  }

  // Priority 4: Show ready state if we have data or completed successfully
  if (ragIndexData || uploadState === 'completed') {
    return 'ready';
  }

  // Priority 5: Default empty state
  return 'empty';
}

export default function RAGIndex() {
  // 🎯 SIMPLIFIED: Use state machine as single source of truth
  const uploadMachine = useUploadMachine();
  const ragIndexData = useRagIndexData();

  const { state, context } = uploadMachine;
  const { ragProgress, lastError } = context;

  // 🎯 SIMPLIFIED: Single function determines UI state
  const uiState = determineUIState(state, ragProgress, lastError, ragIndexData);

  // 🎯 SIMPLIFIED: Clear switch statement for rendering
  switch (uiState) {
    case 'progress':
      return (
        <Card>
          <CardHeader>
            <CardTitle>RAG Index</CardTitle>
            <CardDescription>
              {ragProgress.phase === 'complete'
                ? 'Search and analyze your Tana data using AI-powered retrieval'
                : 'Building searchable index from your Tana data'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ProgressDisplay progress={ragProgress} />
          </CardContent>
        </Card>
      );

    case 'error':
      return (
        <div className="flex items-center justify-center h-full w-full bg-background">
          <Card className="max-w-md">
            <CardHeader>
              <CardTitle className="text-red-600">RAG Index Error</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-4">
                <div className="space-y-2">
                  <div className="text-sm text-red-600 whitespace-pre-wrap">{lastError}</div>
                  <div className="text-xs text-muted-foreground">
                    Please check your configuration and try again.
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      );

    case 'loading':
      return (
        <Card>
          <CardHeader>
            <CardTitle>RAG Index</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center min-h-[300px] text-muted-foreground">
              <div className="flex items-center space-x-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Initializing RAG index...</span>
              </div>
            </div>
          </CardContent>
        </Card>
      );

    case 'ready':
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
                <div className="text-lg">✅ Index Ready</div>
                <div className="text-sm">
                  Your Tana data has been indexed and is ready for AI-powered search.
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      );

    case 'empty':
    default:
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
                <div className="text-lg">No index available</div>
                <div className="text-sm">
                  Use the upload controls to generate a searchable index from your Tana data.
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      );
  }
}
