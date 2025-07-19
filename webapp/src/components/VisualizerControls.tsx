import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import TanaFileUpload from "./ui/TanaFileUpload";
import axios from 'axios';

import { GraphData } from 'react-force-graph-3d';
// Updated to use Zustand store instead of React Context
import { useAppStore, useAppActions } from "../hooks/useAppStore";

// Server-side Visualizer configuration - matches service/service/tana_types.py
interface VisualizerConfig {
  include_tag_tag_links: boolean;
  include_node_tag_links: boolean;
  include_inline_refs: boolean;
  include_inline_ref_nodes: boolean;
  include_content_nodes: boolean;
  include_tag_schema_links: boolean;
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
  const [rawFileData, setRawFileData] = useState<any>(null);
  const [config, setConfig] = useState<VisualizerConfig>({ 
    include_tag_tag_links: true,
    include_node_tag_links: true,
    include_inline_refs: true,
    include_inline_ref_nodes: true,
    include_content_nodes: false,
    include_tag_schema_links: false
  });

  // Custom upload handler that stores the file data for regeneration
  const handleUploadSuccess = (data: TanaGraphData, rawData?: any) => {
    console.log("Graph data received:", data);
    setGraphData(data);
    clearError();
    
    // Store the raw file data for automatic re-upload on config changes
    if (rawData) {
      setRawFileData(rawData);
      console.log("Raw file data stored for automatic re-upload");
    }
  };

  const handleUploadError = (errorMessage: string) => {
    setError(errorMessage);
  };

  // Handle config changes and automatically regenerate graph
  const handleConfigChange = async (key: keyof VisualizerConfig, value: boolean) => {
    const newConfig = { ...config, [key]: value };
    setConfig(newConfig);
    
    // If we have raw file data, automatically regenerate with new config
    if (rawFileData) {
      await regenerateGraphWithConfig(newConfig);
    }
  };

  // Regenerate graph with new configuration
  const regenerateGraphWithConfig = async (newConfig: VisualizerConfig) => {
    if (!rawFileData) {
      setError("No file data available for regeneration. Please upload a file first.");
      return;
    }

    console.log("Automatically regenerating graph with config:", newConfig);
    setLoading(true);
    clearError();

    try {
      // Add the visualizer config to the file data
      const dataWithConfig = {
        ...rawFileData,
        visualize: newConfig
      };

      const response = await axios.post('/graph', dataWithConfig, {
        headers: {
          "Content-Type": "application/json",
        }
      });

      console.log("Graph regenerated successfully:", response.data);
      setGraphData(response.data);
    } catch (error: any) {
      console.error("Failed to regenerate graph:", error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to regenerate graph';
      setError(`Failed to regenerate graph: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
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

      {/* Display Options */}
      {(graphData || loading) && (
        <Card>
          <CardHeader>
            <CardTitle>Display Options</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 2D/3D Toggle */}
            <div>
              <label className="text-sm font-medium mb-2 block">View Mode</label>
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
            </div>

            {/* Graph Configuration Options */}
            <div>
              <label className="text-sm font-medium mb-3 block">Graph Elements</label>
              <div className="space-y-3">
                <div className="text-xs text-muted-foreground mb-2 p-2 bg-muted/50 rounded">
                  <strong>Live Configuration:</strong> Changes are automatically applied to your visualization.
                </div>
                
                {/* Include Tag-Tag Links */}
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="include_tag_tag_links"
                    checked={config.include_tag_tag_links}
                    onChange={(e) => handleConfigChange('include_tag_tag_links', e.target.checked)}
                    disabled={loading || !rawFileData}
                    className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded disabled:opacity-50"
                  />
                  <label htmlFor="include_tag_tag_links" className="text-sm text-foreground">
                    Include tag-to-tag links
                  </label>
                </div>

                {/* Include Node-Tag Links */}
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="include_node_tag_links"
                    checked={config.include_node_tag_links}
                    onChange={(e) => handleConfigChange('include_node_tag_links', e.target.checked)}
                    disabled={loading || !rawFileData}
                    className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded disabled:opacity-50"
                  />
                  <label htmlFor="include_node_tag_links" className="text-sm text-foreground">
                    Include node-to-tag links
                  </label>
                </div>

                {/* Include Inline References */}
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="include_inline_refs"
                    checked={config.include_inline_refs}
                    onChange={(e) => handleConfigChange('include_inline_refs', e.target.checked)}
                    disabled={loading || !rawFileData}
                    className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded disabled:opacity-50"
                  />
                  <label htmlFor="include_inline_refs" className="text-sm text-foreground">
                    Include inline references
                  </label>
                </div>

                {/* Include Inline Reference Nodes */}
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="include_inline_ref_nodes"
                    checked={config.include_inline_ref_nodes}
                    onChange={(e) => handleConfigChange('include_inline_ref_nodes', e.target.checked)}
                    disabled={loading || !rawFileData}
                    className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded disabled:opacity-50"
                  />
                  <label htmlFor="include_inline_ref_nodes" className="text-sm text-foreground">
                    Include inline reference nodes
                  </label>
                </div>

                {/* Include Content Nodes */}
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="include_content_nodes"
                    checked={config.include_content_nodes}
                    onChange={(e) => handleConfigChange('include_content_nodes', e.target.checked)}
                    disabled={loading || !rawFileData}
                    className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded disabled:opacity-50"
                  />
                  <label htmlFor="include_content_nodes" className="text-sm text-foreground">
                    Include content nodes
                  </label>
                </div>

                {/* Include Tag Schema Links */}
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="include_tag_schema_links"
                    checked={config.include_tag_schema_links}
                    onChange={(e) => handleConfigChange('include_tag_schema_links', e.target.checked)}
                    disabled={loading || !rawFileData}
                    className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded disabled:opacity-50"
                  />
                  <label htmlFor="include_tag_schema_links" className="text-sm text-foreground">
                    Include tag schema links
                  </label>
                </div>
              </div>
            </div>

            {/* Search */}
            {graphData && (
              <div>
                <label className="text-sm font-medium mb-2 block">Search Nodes</label>
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
