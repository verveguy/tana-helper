// React import not needed for JSX in React 17+
import TanaStreamingUpload from './ui/TanaStreamingUpload';
// Replace context with Zustand store
import { useAppStore, useAppActions } from '../hooks/useAppStore';

export default function RAGIndexControls() {
  const { ragLoading, ragProgress } = useAppStore();
  const { setRagIndexData, setRagLoading, setRagError } = useAppActions();

  // Note: Removed automatic state reset - global state should persist across component lifecycle

  const handleUploadSuccess = (data: any) => {
    console.log('RAG index streaming completed:', data);
    setRagIndexData(data);
    setRagError(null); // Clear RAG-specific error
    setRagLoading(false); // Ensure loading state is cleared
  };

  const handleUploadError = (errorMessage: string) => {
    setRagError(errorMessage); // Set RAG-specific error
    setRagLoading(false); // Ensure loading state is cleared
  };

  // Don't show the upload interface if we're currently processing
  const isProcessing = ragProgress.isActive && ragProgress.phase !== 'idle' && ragProgress.phase !== 'complete';

  return (
    <TanaStreamingUpload
      endpoint="/chroma/preload"
      onSuccess={handleUploadSuccess}
      onError={handleUploadError}
      disabled={ragLoading || isProcessing}
    />
  );
}
