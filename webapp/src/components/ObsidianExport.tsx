/*

  Export Tana workspace data to Obsidian vault format.

*/

// React import not needed for JSX in React 17+
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Loader2 } from 'lucide-react';
import ProgressDisplay from './ui/ProgressDisplay';

// Replace context with Zustand store
import { useUploadMachine, useObsidianExportData } from '../hooks/useAppStore';

// 🎯 SIMPLIFIED: Clear UI state hierarchy
type UIState =
  | 'progress' // Show progress display during active processing
  | 'error' // Show error state
  | 'loading' // Show loading spinner (fallback)
  | 'ready' // Show completed/ready state
  | 'empty'; // Show empty state

function determineUIState(
  uploadState: string,
  obsidianProgress: any,
  lastError: string | null,
  obsidianExportData: any
): UIState {
  // Priority 1: Show progress during active processing or just completed
  if (obsidianProgress.isActive || obsidianProgress.phase === 'complete') {
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
  if (obsidianExportData || uploadState === 'completed') {
    return 'ready';
  }

  // Priority 5: Default empty state
  return 'empty';
}

export default function ObsidianExport() {
  // 🎯 SIMPLIFIED: Use state machine as single source of truth
  const uploadMachine = useUploadMachine();
  const obsidianExportData = useObsidianExportData();

  const { state, context } = uploadMachine;
  const { obsidianProgress, lastError } = context;

  // 🎯 SIMPLIFIED: Single function determines UI state
  const uiState = determineUIState(state, obsidianProgress, lastError, obsidianExportData);

  // 🎯 SIMPLIFIED: Clear switch statement for rendering
  switch (uiState) {
    case 'progress':
      return (
        <Card>
          <CardHeader>
            <CardTitle>Obsidian Export</CardTitle>
            <CardDescription>
              {obsidianProgress.phase === 'complete'
                ? 'Your Tana data has been exported to an Obsidian vault'
                : 'Converting your Tana data to Obsidian vault format'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ProgressDisplay progress={obsidianProgress} type="obsidian" />
          </CardContent>
        </Card>
      );

    case 'error':
      return (
        <div className="flex items-center justify-center h-full w-full bg-background">
          <Card className="max-w-md">
            <CardHeader>
              <CardTitle className="text-red-600">Obsidian Export Error</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-4">
                <div className="space-y-2">
                  <div className="text-sm text-red-600 whitespace-pre-wrap">{lastError}</div>
                  <div className="text-xs text-muted-foreground">
                    Please check your Tana data and try again.
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
            <CardTitle>Obsidian Export</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center min-h-[300px] text-muted-foreground">
              <div className="flex items-center space-x-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Initializing Obsidian export...</span>
              </div>
            </div>
          </CardContent>
        </Card>
      );

    case 'ready':
      return (
        <Card>
          <CardHeader>
            <CardTitle>Obsidian Export</CardTitle>
            <CardDescription>
              Convert your Tana workspace to an Obsidian vault with markdown files
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center text-muted-foreground py-8">
              <div className="space-y-2">
                <div className="text-lg">🗂️ Export Complete</div>
                <div className="text-sm">
                  Your Tana data has been exported to an Obsidian vault in your home directory.
                </div>
                <div className="text-xs text-muted-foreground mt-4">
                  Check the ~/vault directory to access your Obsidian vault.
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
            <CardTitle>Obsidian Export</CardTitle>
            <CardDescription>
              Convert your Tana workspace to an Obsidian vault with markdown files
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center text-muted-foreground py-8">
              <div className="space-y-2">
                <div className="text-lg">No export available</div>
                <div className="text-sm">
                  Upload your Tana JSON export to generate an Obsidian vault with:
                </div>
                <div className="text-xs text-left mt-4 space-y-1 max-w-md mx-auto">
                  <div>• Markdown files for each topic</div>
                  <div>• Frontmatter with metadata and fields</div>
                  <div>• Obsidian-compatible reference links</div>
                  <div>• Pre-configured plugins and settings</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      );
  }
}
