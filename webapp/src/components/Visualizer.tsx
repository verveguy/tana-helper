/*

  Visualize a Tana Workspace in #d

  Thanks to the amazing https://github.com/vasturiano/react-force-graph

*/


import React, { useMemo, useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import ForceGraph3D from 'react-force-graph-3d';
import ForceGraph2D from 'react-force-graph-2d';
import { Loader2 } from 'lucide-react';

// Replace context with Zustand store
import { useGraphData, useLoading, useTwoDee, useError } from "../hooks/useAppStore";

// Debounce utility to prevent excessive resize calculations
const debounce = (func: Function, wait: number) => {
  let timeout: NodeJS.Timeout;
  return function executedFunction(...args: any[]) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

export default function Visualizer() {
  // Use Zustand hooks instead of context
  const graphData = useGraphData();
  const loading = useLoading(); 
  const twoDee = useTwoDee();
  const error = useError();

  // Track viewport dimensions for full-screen visualization
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // Memoized dimension calculation to prevent unnecessary recalculations
  const calculateDimensions = useCallback(() => {
    const sidebarWidth = 240; // 60 * 4 = 240px (w-60 in Tailwind)
    const availableWidth = window.innerWidth - sidebarWidth;
    const availableHeight = window.innerHeight;
    
    return {
      width: availableWidth,
      height: availableHeight
    };
  }, []);

  // Debounced dimension update to prevent excessive re-renders during resize
  const debouncedUpdateDimensions = useMemo(
    () => debounce(() => {
      const newDimensions = calculateDimensions();
      setDimensions(prevDimensions => {
        // Only update if dimensions actually changed significantly (avoid tiny changes)
        if (
          Math.abs(prevDimensions.width - newDimensions.width) > 10 ||
          Math.abs(prevDimensions.height - newDimensions.height) > 10
        ) {
          return newDimensions;
        }
        return prevDimensions; // Return same reference to prevent re-render
      });
    }, 100), // 100ms debounce
    [calculateDimensions]
  );

  // Update dimensions on mount and resize
  useEffect(() => {
    // Set initial dimensions
    setDimensions(calculateDimensions());

    // Listen for window resize with debouncing
    window.addEventListener('resize', debouncedUpdateDimensions);
    return () => window.removeEventListener('resize', debouncedUpdateDimensions);
  }, [calculateDimensions, debouncedUpdateDimensions]);

  // Memoize the graph data to prevent unnecessary re-renders
  const memoizedGraphData = useMemo(() => graphData, [graphData]);

  // Memoize common props to prevent creating new objects on every render
  const commonProps = useMemo(() => ({
    graphData: memoizedGraphData,
    nodeLabel: 'name',
    nodeAutoColorBy: 'group',
    linkDirectionalParticles: 2,
    linkDirectionalParticleSpeed: 0.006,
    backgroundColor: '#000000',
    width: dimensions.width,
    height: dimensions.height,
  }), [memoizedGraphData, dimensions.width, dimensions.height]);

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

  return (
    <div className="relative h-full w-full bg-black">
      {/* Title overlay - memoized to prevent re-renders */}
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