// React import not needed for JSX in React 17+
import TanaFileUpload from './ui/TanaFileUpload';
// Replace context with Zustand store
import { useAppStore, useAppActions } from '../hooks/useAppStore';

export default function RAGIndexControls() {
  const { ragLoading } = useAppStore();
  const { setRagIndexData, setRagLoading, setRagError } = useAppActions();

  // Note: Removed automatic state reset - global state should persist across component lifecycle

  const handleUploadSuccess = (data: any, _rawFileData?: any) => {
    console.log('RAG index data received:', data);
    setRagIndexData(data);
    setRagError(null); // Clear RAG-specific error
    // Note: rawFileData not needed for RAG index as it doesn't have live config changes
  };

  const handleUploadError = (errorMessage: string) => {
    setRagError(errorMessage); // Set RAG-specific error
  };

  return (
    <TanaFileUpload
      endpoint="/rag_index"
      uploadType="json"
      onSuccess={handleUploadSuccess}
      onError={handleUploadError}
      loading={ragLoading}
      setLoading={setRagLoading}
    />
  );
}
