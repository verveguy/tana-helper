/*

  Visualize a Tana Workspace in #d

  Thanks to the amazing https://github.com/vasturiano/react-force-graph

*/


import React, { useMemo, useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import ForceGraph3D from 'react-force-graph-3d';
import ForceGraph2D from 'react-force-graph-2d';
import { Loader2 } from 'lucide-react';

// Replace context with Zustand store
import { useGraphData, useLoading, useTwoDee, useError } from "../hooks/useAppStore";

export default function Visualizer() {
  // Use Zustand hooks instead of context
  const graphData = useGraphData();
  const loading = useLoading(); 
  const twoDee = useTwoDee();
  const error = useError();

  // Track viewport dimensions for full-screen visualization
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // Update dimensions on mount and resize
  useEffect(() => {
    const updateDimensions = () => {
      // Calculate available space (full viewport minus sidebar width)
      const sidebarWidth = 240; // 60 * 4 = 240px (w-60 in Tailwind)
      const availableWidth = window.innerWidth - sidebarWidth;
      const availableHeight = window.innerHeight;
      
      setDimensions({
        width: availableWidth,
        height: availableHeight
      });
    };

    // Set initial dimensions
    updateDimensions();

    // Listen for window resize
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Memoize the graph data to prevent unnecessary re-renders
  const memoizedGraphData = useMemo(() => graphData, [graphData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full w-full bg-background">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="text-lg">Loading visualization...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full w-full bg-background">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Visualization Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!memoizedGraphData || !memoizedGraphData.nodes || memoizedGraphData.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full w-full bg-background">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>Graph Visualizer</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center text-muted-foreground py-8">
              <div className="space-y-2">
                <div className="text-lg">No graph data available</div>
                <div className="text-sm">
                  Use the controls to generate a visualization from your Tana data.
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const commonProps = {
    graphData: memoizedGraphData,
    nodeLabel: 'name',
    nodeAutoColorBy: 'group',
    linkDirectionalParticles: 2,
    linkDirectionalParticleSpeed: 0.006,
    backgroundColor: '#000000',
    width: dimensions.width,
    height: dimensions.height,
  };

  return (
    <div className="relative h-full w-full bg-black">
      {/* Title overlay */}
      <div className="absolute top-4 left-4 z-10 bg-black/80 px-3 py-2 rounded-lg border border-gray-700">
        <h2 className="text-lg font-semibold text-white">
          Graph Visualizer ({twoDee ? '2D' : '3D'})
        </h2>
        <p className="text-sm text-gray-300">
          Interactive visualization of your Tana data relationships
        </p>
      </div>

      {/* Full-screen visualization */}
      {twoDee ? (
        <ForceGraph2D {...commonProps} />
      ) : (
        <ForceGraph3D {...commonProps} />
      )}
    </div>
  );
}