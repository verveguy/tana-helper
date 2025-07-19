import React, { SyntheticEvent, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Upload, Loader2 } from "lucide-react";

import { GraphData } from 'react-force-graph-3d';
import axios from 'axios';
// import FlexSearch from "flexsearch-ts";
// Updated to use Zustand store instead of React Context
import { useAppStore, useGraphActions, useAppActions } from "../hooks/useAppStore";

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
  
  const [open, setOpen] = useState(true);
  const [rawGraphData, setRawGraphData] = useState<TanaGraphData>();
  const [config, setConfig] = useState<GraphConfig>({ 
    include_all_nodes: true, 
    include_tag_nodes: false, 
    include_tag_links: false, 
    include_inline_ref_nodes: false, 
    include_inline_refs: false 
  });
  const [dumpFile, setDumpFile] = useState<File>();
  const [upload, setUpload] = useState(false);
  const [searchString, setSearchString] = useState('');
  // const [index, setIndex] = useState(new FlexSearch({ preset: "match" } as any));

  const handleFileUpload = (event: React.FormEvent<HTMLInputElement>) => {
    const target = event.currentTarget;
    const file = target.files?.[0];
    if (file) {
      console.log("File selected:", file.name, file.size, file.type);
      setDumpFile(file);
      setUpload(true);
    }
    event.currentTarget.value = "";
  };

  useEffect(() => {
    if (upload && dumpFile) {
      console.log("Starting file upload...");
      clearError();
      setLoading(true);
      
      // Read the file content as text since server expects JSON
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const fileContent = event.target?.result as string;
          const jsonData = JSON.parse(fileContent);
          console.log("File parsed successfully, sending to server...");
          
          axios.post('/graph', jsonData, {
            headers: {
              "Content-Type": "application/json",
            }
          })
            .then(response => {
              console.log("Upload successful, response:", response.data);
              const new_graph = response.data as TanaGraphData;
              setRawGraphData(new_graph);
              
              // Build search index
              // if (new_graph) {
              //   const index = new FlexSearch({ preset: "match" } as any);
              //   new_graph.nodes.forEach((node) => {
              //     index.add(node.id as string, node.name);
              //   });
              //   setIndex(index);
              // }
              
              setGraphData(new_graph);
              console.log("Graph data set successfully");
            })
            .catch(error => {
              console.error("Upload failed:", error);
              const errorMessage = error.response?.data?.detail || error.message || 'Upload failed';
              setError(`Failed to process file: ${errorMessage}`);
            })
            .finally(() => {
              setLoading(false);
              setUpload(false);
            });
        } catch (parseError) {
          console.error("Failed to parse JSON file:", parseError);
          setError("Invalid JSON file. Please check your file format.");
          setLoading(false);
          setUpload(false);
        }
      };
      
      reader.onerror = () => {
        console.error("Failed to read file");
        setError("Failed to read file. Please try again.");
        setLoading(false);
        setUpload(false);
      };
      
      reader.readAsText(dumpFile);
    }
  }, [upload, dumpFile, setLoading, setGraphData, setError, clearError]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Visualizer Controls</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* File Upload */}
        <div>
          <div className="flex items-center space-x-2 mb-2">
            <Input
              type="file"
              accept=".json"
              onChange={handleFileUpload}
              disabled={loading}
              className="flex-1"
            />
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
          </div>
          <p className="text-xs text-muted-foreground">
            Upload Tana JSON export to visualize your workspace
          </p>
        </div>

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

        {/* Status messages */}
        {loading && (
          <div className="text-sm text-muted-foreground flex items-center space-x-2">
            <Loader2 className="h-3 w-3 animate-spin" />
            <span>Processing file...</span>
          </div>
        )}

        {/* Error display */}
        {error && (
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
        )}
      </CardContent>
    </Card>
  );
}
