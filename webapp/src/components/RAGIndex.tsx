/*

  Visualize a Tana workspace tags as a class diagram.

*/

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Loader2 } from "lucide-react";

// Replace context with Zustand store
import { useRagIndexData, useLoading } from "../hooks/useAppStore";

export default function RAGIndex() {
  // Use Zustand hooks instead of context
  const ragIndexData = useRagIndexData();
  const loading = useLoading();

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

  return (
    <Card>
      <CardHeader>
        <CardTitle>RAG Index</CardTitle>
        <CardDescription>
          Search and analyze your Tana data using AI-powered retrieval
        </CardDescription>
      </CardHeader>
      <CardContent>
        {ragIndexData ? (
          <div className="space-y-4">
            <div className="text-sm text-muted-foreground">
              Index contains {ragIndexData.documents?.length || 0} documents
            </div>
            <pre className="bg-muted p-4 rounded-lg text-sm overflow-auto max-h-96">
              {JSON.stringify(ragIndexData, null, 2)}
            </pre>
          </div>
        ) : (
          <div className="text-center text-muted-foreground py-8">
            No RAG index data available. Use the controls to generate an index.
          </div>
        )}
      </CardContent>
    </Card>
  );
}

