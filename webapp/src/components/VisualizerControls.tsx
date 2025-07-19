import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import TanaFileUpload from "./ui/TanaFileUpload";

import { GraphData } from 'react-force-graph-3d';
// Updated to use Zustand store instead of React Context
import { useAppStore, useAppActions } from "../hooks/useAppStore";

interface GraphConfig {
  include_all_nodes: boolean;
  include_tag_nodes: boolean;
  include_tag_links: boolean;
  include_inline_refs: boolean;
  include_inline_ref_nodes: boolean;
}

// Define our expected graph data structure
interface TanaGraphData extends GraphData {
  nodes: Array<{ id: string; name: string; [key: string]: any }>;
  links: Array<{ source: string; target: string; [key: string]: any }>;
}

export default function VisualizerControls() {
  const { graphData, loading, twoDee, error } = useAppStore();
  const { setGraphData, setTwoDee, setLoading, setError, clearError } = useAppActions();
  
  const [searchString, setSearchString] = useState('');

  const handleUploadSuccess = (data: TanaGraphData) => {
    console.log("Graph data received:", data);
    setGraphData(data);
    clearError();
  };

  const handleUploadError = (errorMessage: string) => {
    setError(errorMessage);
  };

  return (
    <>
      {/* File Upload */}
      <TanaFileUpload
        title="Visualizer Controls"
        description="Upload Tana JSON export to visualize your workspace"
        buttonText="Generate Visualization"
        endpoint="/graph"
        uploadType="json"
        onSuccess={handleUploadSuccess}
        onError={handleUploadError}
        loading={loading}
        setLoading={setLoading}
      />

      {/* Additional Controls */}
      {(graphData || loading) && (
        <Card>
          <CardHeader>
            <CardTitle>Display Options</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 2D/3D Toggle */}
            <div className="flex items-center space-x-2">
              <Button
                variant={twoDee ? "default" : "outline"}
                size="sm"
                onClick={() => setTwoDee(true)}
                disabled={loading}
              >
                2D
              </Button>
              <Button
                variant={!twoDee ? "default" : "outline"}
                size="sm"
                onClick={() => setTwoDee(false)}
                disabled={loading}
              >
                3D
              </Button>
            </div>

            {/* Search */}
            {graphData && (
              <div>
                <Input
                  placeholder="Search nodes..."
                  value={searchString}
                  onChange={(e) => setSearchString(e.target.value)}
                  disabled={loading}
                />
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Error display */}
      {error && (
        <Card>
          <CardContent className="pt-6">
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-start justify-between">
                <div className="text-sm text-red-800">
                  {error}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearError}
                  className="text-red-600 hover:text-red-800 -mt-1 -mr-1"
                >
                  ×
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </>
  );
}
