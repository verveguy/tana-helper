import React from "react";
import TanaFileUpload from "./ui/TanaFileUpload";
// Replace context with Zustand store
import { useAppStore, useAppActions } from "../hooks/useAppStore";

export default function RAGIndexControls() {
  const { loading, error } = useAppStore();
  const { setRagIndexData, setLoading, setError, clearError } = useAppActions();

  const handleUploadSuccess = (data: any) => {
    console.log("RAG index data received:", data);
    setRagIndexData(data);
    clearError();
  };

  const handleUploadError = (errorMessage: string) => {
    setError(errorMessage);
  };

  return (
    <TanaFileUpload
      title="RAG Index Generator"
      description="Upload a Tana JSON export to generate a searchable index for retrieval-augmented generation"
      buttonText="Generate RAG Index"
      endpoint="/rag_index"
      uploadType="json"
      onSuccess={handleUploadSuccess}
      onError={handleUploadError}
      loading={loading}
      setLoading={setLoading}
    />
  );
}
