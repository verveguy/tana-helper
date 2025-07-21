/*

  Visualize a Tana workspace tags as a class diagram.

*/

// React import not needed for JSX in React 17+
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Loader2 } from 'lucide-react';

// Replace context with Zustand store
import { useRagIndexData, useRagLoading, useRagError } from '../hooks/useAppStore';

export default function RAGIndex() {
  // Use Zustand hooks instead of context
  const ragIndexData = useRagIndexData();
  const loading = useRagLoading();
  const error = useRagError();

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

  return (
    <Card>
      <CardHeader>
        <CardTitle>RAG Index</CardTitle>
        <CardDescription>
          Search and analyze your Tana data using AI-powered retrieval
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground">
            Index contains {ragIndexData.documents?.length || 0} documents
          </div>
          <pre className="bg-muted p-4 rounded-lg text-sm overflow-auto max-h-96">
            {JSON.stringify(ragIndexData, null, 2)}
          </pre>
        </div>
      </CardContent>
    </Card>
  );
}
