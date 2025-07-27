// React import not needed for JSX in React 17+
import TanaStreamingUpload from './ui/TanaStreamingUpload';
// Replace context with Zustand store
import { useUploadMachine, useUploadActions } from '../hooks/useAppStore';

// 🎯 SIMPLIFIED: Helper function to determine if upload should be disabled
function shouldDisableUpload(uploadState: string, ragProgress: any): boolean {
  // Disable during active upload/processing states
  if (uploadState === 'uploading' || uploadState === 'processing' || uploadState === 'cancelling') {
    return true;
  }

  // Disable during active RAG progress (except when idle or complete)
  if (ragProgress.isActive && ragProgress.phase !== 'idle' && ragProgress.phase !== 'complete') {
    return true;
  }

  return false;
}

export default function RAGIndexControls() {
  const uploadMachine = useUploadMachine();
  // Note: Upload actions are handled internally by TanaStreamingUpload
  // const uploadActions = useUploadActions(); // Not needed here

  const { state, context } = uploadMachine;
  const { ragProgress } = context;

  const handleUploadSuccess = (data: any) => {
    console.log('RAG index streaming completed:', data);
    // Note: completeUpload is already called by TanaStreamingUpload component
    // This callback is just for additional success handling if needed
  };

  const handleUploadError = (errorMessage: string) => {
    console.error('RAG index upload failed:', errorMessage);
    // Note: errorUpload is already called by TanaStreamingUpload component
    // This callback is just for additional error handling if needed
  };

  // 🎯 SIMPLIFIED: Clear disable logic
  const isUploadDisabled = shouldDisableUpload(state, ragProgress);

  return (
    <TanaStreamingUpload
      endpoint="/chroma/preload"
      onSuccess={handleUploadSuccess}
      onError={handleUploadError}
      disabled={isUploadDisabled}
    />
  );
}
