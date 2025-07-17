/*

  Visualize a Tana Workspace in #d

  Thanks to the amazing https://github.com/vasturiano/react-force-graph

*/


import React, { useEffect, useMemo } from 'react';
import { Card, CardContent, Typography, CircularProgress } from '@mui/material';
import ForceGraph3D from 'react-force-graph-3d';
import ForceGraph2D from 'react-force-graph-2d';

// Replace context with Zustand store
import { useGraphData, useLoading, useTwoDee } from "../hooks/useAppStore";

export default function Visualizer() {
  // Use Zustand hooks instead of context
  const graphData = useGraphData();
  const loading = useLoading(); 
  const twoDee = useTwoDee();

  // Memoize the graph data to prevent unnecessary re-renders
  const memoizedGraphData = useMemo(() => graphData, [graphData]);

  if (loading) {
    return (
      <Card>
        <CardContent>
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
            <CircularProgress />
            <Typography variant="body1" style={{ marginLeft: '16px' }}>
              Loading visualization...
            </Typography>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!memoizedGraphData || !memoizedGraphData.nodes || memoizedGraphData.nodes.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Graph Visualizer
          </Typography>
          <Typography color="textSecondary">
            No graph data available. Use the controls to generate a visualization.
          </Typography>
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
    width: window.innerWidth * 0.7,
    height: window.innerHeight * 0.8,
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Graph Visualizer ({twoDee ? '2D' : '3D'})
        </Typography>
        <div style={{ display: 'flex', justifyContent: 'center' }}>
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