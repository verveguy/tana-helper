import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
// Replace context with Zustand store
import { useAppActions } from "../hooks/useAppStore";

export default function RAGIndexControls() {
  const { setRagIndexData, setLoading } = useAppActions();

  const handleGenerateIndex = () => {
    setLoading(true);
    // Placeholder for RAG index generation
    setTimeout(() => {
      setRagIndexData({ documents: [] });
      setLoading(false);
    }, 1000);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>RAG Index Controls</CardTitle>
      </CardHeader>
      <CardContent>
        <Button onClick={handleGenerateIndex} className="w-full">
          Generate RAG Index
        </Button>
      </CardContent>
    </Card>
  );
}
