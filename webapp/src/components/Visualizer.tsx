/*

  Visualize a Tana Workspace in #d

  Thanks to the amazing https://github.com/vasturiano/react-force-graph

*/


import React, { useMemo } from 'react';
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

  // Memoize the graph data to prevent unnecessary re-renders
  const memoizedGraphData = useMemo(() => graphData, [graphData]);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Graph Visualizer</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center min-h-[400px] text-muted-foreground">
            <div className="flex items-center space-x-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Loading visualization...</span>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Graph Visualizer</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-red-600 py-12">
            <div className="space-y-2">
              <div className="text-lg font-medium">Error</div>
              <div className="text-sm">
                {error}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!memoizedGraphData || !memoizedGraphData.nodes || memoizedGraphData.nodes.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Graph Visualizer</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-12">
            <div className="space-y-2">
              <div className="text-lg">No graph data available</div>
              <div className="text-sm">
                Use the controls to generate a visualization from your Tana data.
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const commonProps = {
    graphData: memoizedGraphData,
    nodeLabel: 'name',
    nodeAutoColorBy: 'group',
    linkDirectionalParticles: 2,
    linkDirectionalParticleSpeed: 0.006,
    backgroundColor: '#000000',
    width: Math.min(window.innerWidth * 0.7, 1200),
    height: Math.min(window.innerHeight * 0.7, 600),
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Graph Visualizer ({twoDee ? '2D' : '3D'})
        </CardTitle>
        <CardDescription>
          Interactive visualization of your Tana data relationships
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex justify-center bg-black rounded-lg overflow-hidden">
          {twoDee ? (
            <ForceGraph2D {...commonProps} />
          ) : (
            <ForceGraph3D {...commonProps} />
          )}
        </div>
      </CardContent>
    </Card>
  );
}