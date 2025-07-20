import React, { useState, useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import TanaFileUpload from './ui/TanaFileUpload';

import { GraphData } from 'react-force-graph-3d';
import { Index } from 'flexsearch';
// Updated to use Zustand store instead of React Context
import { useAppStore, useAppActions } from '../hooks/useAppStore';

// Server-side Visualizer configuration - matches service/service/tana_types.py
interface VisualizerConfig {
  include_all_nodes: boolean;
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
  const { graphData, visualizerLoading, twoDee, visualizerError } = useAppStore();
  const { setGraphData, setTwoDee, setVisualizerLoading, setVisualizerError } = useAppActions();

  const [searchString, setSearchString] = useState('');
  const [rawGraphData, setRawGraphData] = useState<any>(null);
  const [searchIndex, setSearchIndex] = useState(new Index({ preset: 'match' }));
  const [config, setConfig] = useState<VisualizerConfig>({
    include_all_nodes: false, // KEY: Only show nodes connected by enabled links
    include_tag_tag_links: true, // Show tag hierarchy relationships
    include_node_tag_links: true, // Show which nodes have which tags
    include_inline_refs: false, // Hide indirect references (reduces noise)
    include_inline_ref_nodes: false, // Hide inline reference nodes (reduces noise)
    include_content_nodes: false, // Hide child content nodes (detail nodes)
    include_tag_schema_links: false, // Hide tag schema relationships
  });

  // Note: Removed automatic state reset - global state should persist across component lifecycle

  // Helper to get ID from polymorphic object (links can be mutated by force graph)
  const getIdFrom = useCallback((obj: any): string => {
    let id: string = obj as string;
    if (id && typeof id !== 'string') {
      id = obj['id'];
    }
    return id;
  }, []);

  // Restored original filtering logic from pre-migration with search integration
  const applyClientSideFiltering = useCallback(
    (data: TanaGraphData, filterConfig: VisualizerConfig, searchStr: string): TanaGraphData => {
      if (!data || !data.links) return data;

      console.log(
        'Applying client-side filtering with config:',
        filterConfig,
        'search:',
        searchStr
      );

      // Debug: Check what link types we're receiving
      const linkTypes = new Set(data.links.map(link => link.reason));
      console.log('Link types in data:', Array.from(linkTypes));

      // Start with a copy of raw data
      let newGraph = { ...data };
      let connectedNodeIds = {};

      // Build search result set if there's a search string
      let searchResultIds = {};
      let hasSearch = searchStr && searchStr.trim() !== '';

      if (hasSearch && searchIndex) {
        const searchResults = searchIndex.search(searchStr.trim());
        console.log(`Search for "${searchStr}" found ${searchResults.length} matches`);

        // Convert search results to a lookup dictionary
        searchResultIds = searchResults.reduce(
          (dict, nodeId) => {
            dict[nodeId as string] = {};
            return dict;
          },
          {} as Record<string, {}>
        );
      }

      // Filter links based on reason codes AND build connected nodes dictionary
      const filteredLinks = data.links.filter((link: any) => {
        let found = false;

        // First check if link type is enabled
        switch (link.reason) {
          case 'itn': // tag-to-tag links
            found = filterConfig.include_tag_tag_links;
            break;
          case 'itl': // node-to-tag links
            found = filterConfig.include_node_tag_links;
            break;
          case 'iir': // indirect/inline reference links
            found = filterConfig.include_inline_refs;
            break;
          case 'iin': // inline reference node links
            found = filterConfig.include_inline_ref_nodes;
            break;
          case 'icl': // content links
            found = filterConfig.include_content_nodes;
            break;
          case 'its': // tag schema links
            found = filterConfig.include_tag_schema_links;
            break;
          default:
            found = false; // Exclude unknown link types
        }

        // If link type is enabled, check search filter
        if (found && hasSearch) {
          const sourceId = getIdFrom(link.source);
          const targetId = getIdFrom(link.target);

          // Only include link if at least one endpoint matches search
          found = sourceId in searchResultIds || targetId in searchResultIds;
        }

        // If this link passed all filters, add its endpoints to connected nodes
        if (found) {
          const sourceId = getIdFrom(link.source);
          const targetId = getIdFrom(link.target);
          connectedNodeIds[sourceId] = {};
          connectedNodeIds[targetId] = {};
        }

        return found;
      });

      newGraph.links = filteredLinks;

      console.log(`Filtered links: ${data.links.length} -> ${filteredLinks.length}`);

      // Filter nodes based on include_all_nodes OR being connected by included links OR search results
      const filteredNodes = data.nodes.filter(node => {
        // If "show all nodes" is checked, show everything (but still respect search)
        if (filterConfig.include_all_nodes) {
          return hasSearch ? node.id && node.id in searchResultIds : true;
        }

        // Otherwise, show nodes that are either:
        // 1. In search results (if searching), OR
        // 2. Connected by enabled links
        if (hasSearch) {
          return node.id && (node.id in searchResultIds || node.id in connectedNodeIds);
        } else {
          return node.id && node.id in connectedNodeIds;
        }
      });

      newGraph.nodes = filteredNodes;

      console.log(`Filtered nodes: ${data.nodes.length} -> ${filteredNodes.length}`);

      return newGraph;
    },
    [getIdFrom, searchIndex]
  );

  // Memoize filtered graph data to prevent unnecessary re-renders
  const filteredGraphData = useMemo(() => {
    if (!rawGraphData) return null;
    return applyClientSideFiltering(rawGraphData, config, searchString);
  }, [rawGraphData, config, searchString, applyClientSideFiltering]);

  // Update graph data only when filtered data actually changes
  React.useEffect(() => {
    if (filteredGraphData) {
      setGraphData(filteredGraphData);
    }
  }, [filteredGraphData, setGraphData]);

  // Upload handler that stores raw data and builds search index
  const handleUploadSuccess = useCallback(
    (data: TanaGraphData, _rawData?: any) => {
      console.log('Graph data received:', data);
      setRawGraphData(data); // Store the raw data with all links

      // Build search index from node names
      if (data && data.nodes) {
        const newIndex = new Index({ preset: 'match' });
        data.nodes.forEach(node => {
          if (node.id && node.name) {
            newIndex.add(node.id, node.name);
          }
        });
        setSearchIndex(newIndex);
        console.log(`Built search index with ${data.nodes.length} nodes`);
      }

      setVisualizerError(null); // Clear visualizer-specific error
    },
    [setVisualizerError]
  );

  const handleUploadError = useCallback(
    (errorMessage: string) => {
      setVisualizerError(errorMessage); // Set visualizer-specific error
    },
    [setVisualizerError]
  );

  // Handle config changes - now memoized to prevent excessive re-renders
  const handleConfigChange = useCallback((key: keyof VisualizerConfig, value: boolean) => {
    setConfig(prevConfig => {
      // Only update if value actually changed
      if (prevConfig[key] === value) {
        return prevConfig; // Return same reference to prevent re-renders
      }

      return {
        ...prevConfig,
        [key]: value,
      };
    });
  }, []);

  return (
    <>
      {/* File Upload */}
      <TanaFileUpload
        endpoint="/graph"
        uploadType="json"
        onSuccess={handleUploadSuccess}
        onError={handleUploadError}
        loading={visualizerLoading}
        setLoading={setVisualizerLoading}
      />

      {/* Display Options */}
      {(graphData || visualizerLoading) && (
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
                  variant={twoDee ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setTwoDee(true)}
                  disabled={visualizerLoading}
                >
                  2D
                </Button>
                <Button
                  variant={!twoDee ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setTwoDee(false)}
                  disabled={visualizerLoading}
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
                  <strong>Live Configuration:</strong> Changes are automatically applied to your
                  visualization.
                </div>

                {/* Show All Nodes - Primary Control */}
                <div className="flex items-center space-x-2 p-2 bg-primary/10 rounded border">
                  <input
                    type="checkbox"
                    id="include_all_nodes"
                    checked={config.include_all_nodes}
                    onChange={e => handleConfigChange('include_all_nodes', e.target.checked)}
                    disabled={visualizerLoading || !rawGraphData}
                    className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded disabled:opacity-50"
                  />
                  <label
                    htmlFor="include_all_nodes"
                    className="text-sm font-medium text-foreground"
                  >
                    Show all nodes (including unconnected detail nodes)
                  </label>
                </div>

                <div className="text-xs text-muted-foreground mb-2">
                  When unchecked, only shows nodes connected by the link types selected below.
                </div>

                {/* Include Tag-Tag Links */}
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="include_tag_tag_links"
                    checked={config.include_tag_tag_links}
                    onChange={e => handleConfigChange('include_tag_tag_links', e.target.checked)}
                    disabled={visualizerLoading || !rawGraphData}
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
                    onChange={e => handleConfigChange('include_node_tag_links', e.target.checked)}
                    disabled={visualizerLoading || !rawGraphData}
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
                    onChange={e => handleConfigChange('include_inline_refs', e.target.checked)}
                    disabled={visualizerLoading || !rawGraphData}
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
                    onChange={e => handleConfigChange('include_inline_ref_nodes', e.target.checked)}
                    disabled={visualizerLoading || !rawGraphData}
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
                    onChange={e => handleConfigChange('include_content_nodes', e.target.checked)}
                    disabled={visualizerLoading || !rawGraphData}
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
                    onChange={e => handleConfigChange('include_tag_schema_links', e.target.checked)}
                    disabled={visualizerLoading || !rawGraphData}
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
                  onChange={e => setSearchString(e.target.value)}
                  disabled={visualizerLoading}
                />
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Error display */}
      {visualizerError && (
        <Card>
          <CardContent className="pt-6">
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-start justify-between">
                <div className="text-sm text-red-800">{visualizerError}</div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setVisualizerError(null)}
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
