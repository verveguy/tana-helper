import React, { SyntheticEvent, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Upload } from "lucide-react";

import { GraphData } from 'react-force-graph-3d';
import axios from 'axios';
import FlexSearch from "flexsearch-ts";
// Updated to use Zustand store instead of React Context
import { useAppStore, useGraphActions, useAppActions } from "../hooks/useAppStore";

interface GraphConfig {
  include_all_nodes: boolean;
  include_tag_nodes: boolean;
  include_tag_links: boolean;
  include_inline_refs: boolean;
  include_inline_ref_nodes: boolean;
}

export default function VisualizerControls() {
  const { graphData, loading, twoDee } = useAppStore();
  const { setGraphData, setTwoDee } = useAppActions();
  
  const [open, setOpen] = useState(true);
  const [rawGraphData, setRawGraphData] = useState<GraphData>();
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
  const [index, setIndex] = useState(new FlexSearch({}));

  const handleFileUpload = (event: React.FormEvent<HTMLInputElement>) => {
    const target = event.currentTarget;
    const file = target.files?.[0];
    setDumpFile(file);
    setUpload(true);
    event.currentTarget.value = "";
  };

  useEffect(() => {
    if (upload && dumpFile) {
      setGraphData(undefined);
      axios.post('/graph_view', dumpFile, {
        headers: {
          "Content-Type": "application/json",
        }
      })
        .then(response => {
          const new_graph = response.data as GraphData;
          setRawGraphData(new_graph);
          
          // Build search index
          if (new_graph) {
            const index = new FlexSearch({ preset: "match" });
            new_graph.nodes.forEach((node) => {
              index.add(node.id as string, node.name);
            });
            setIndex(index);
          }
          
          setGraphData(new_graph);
        })
        .catch(error => {
          console.error(error);
        })
        .finally(() => {
          setUpload(false);
        });
    }
  }, [upload, dumpFile]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Visualizer Controls</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* File Upload */}
        <div>
          <Input
            type="file"
            accept=".json"
            onChange={handleFileUpload}
            className="mb-2"
          />
          <p className="text-xs text-muted-foreground">Upload Tana JSON export</p>
        </div>

        {/* 2D/3D Toggle */}
        <div className="flex items-center space-x-2">
          <Button
            variant={twoDee ? "default" : "outline"}
            size="sm"
            onClick={() => setTwoDee(true)}
          >
            2D
          </Button>
          <Button
            variant={!twoDee ? "default" : "outline"}
            size="sm"
            onClick={() => setTwoDee(false)}
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
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
