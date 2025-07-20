import React, { useEffect } from "react";
import TanaFileUpload from "./ui/TanaFileUpload";
// Replace context with Zustand store
import { useAppStore, useAppActions } from "../hooks/useAppStore";

export default function ClassDiagramControls() {
  // Use Zustand actions instead of context
  const { classLoading, classError } = useAppStore();
  const { setMermaidText, setClassLoading, setClassError } = useAppActions();

  // Note: Removed automatic state reset - global state should persist across component lifecycle

  const handleUploadSuccess = (data: string, rawFileData?: any) => {
    console.log("Class diagram data received:", data);
    setMermaidText(data);
    setClassError(null); // Clear class-specific error
    // Note: rawFileData not needed for class diagrams as they don't have live config changes
  };

  const handleUploadError = (errorMessage: string) => {
    setClassError(errorMessage); // Set class-specific error
  };

  return (
    <TanaFileUpload
      endpoint="/mermaid_classes"
      uploadType="json"
      onSuccess={handleUploadSuccess}
      onError={handleUploadError}
      loading={classLoading}
      setLoading={setClassLoading}
    />
  );
}
