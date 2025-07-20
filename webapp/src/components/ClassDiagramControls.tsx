import React from "react";
import TanaFileUpload from "./ui/TanaFileUpload";
// Replace context with Zustand store
import { useAppStore, useAppActions } from "../hooks/useAppStore";

export default function ClassDiagramControls() {
  // Use Zustand actions instead of context
  const { loading, error } = useAppStore();
  const { setMermaidText, setLoading, setError, clearError } = useAppActions();

  const handleUploadSuccess = (data: string, rawFileData?: any) => {
    console.log("Class diagram data received:", data);
    setMermaidText(data);
    clearError();
    // Note: rawFileData not needed for class diagrams as they don't have live config changes
  };

  const handleUploadError = (errorMessage: string) => {
    setError(errorMessage);
  };

  return (
    <TanaFileUpload
      endpoint="/mermaid_classes"
      uploadType="json"
      onSuccess={handleUploadSuccess}
      onError={handleUploadError}
      loading={loading}
      setLoading={setLoading}
    />
  );
}
