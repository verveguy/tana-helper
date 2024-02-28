/*

  Visualize a Tana Workspace in #d

  Thanks to the amazing https://github.com/vasturiano/react-force-graph

*/


import React, { useCallback, useContext, useRef } from "react";
import { CircularProgress } from '@mui/material';
import ForceGraph3D from 'react-force-graph-3d';
import ForceGraph2D from 'react-force-graph-2d';
import { TanaHelperContext } from "../TanaHelperContext";
import { useDimensions } from "./utils";
import './Visualizer.css';

export default function Visualizer() {
  const containerRef = useRef(null);
  const dimensions = useDimensions(containerRef);
  const { graphData, loading, twoDee } = useContext(TanaHelperContext)
  const fgRef = useRef(null);

  // TODO: rework this to be cleaner React.
  // See example:
  // https://github.com/vasturiano/react-force-graph/blob/master/example/click-to-focus/index.html
  const handleNodeClick = useCallback(node => {
    // Aim at node from outside it
    const distance = 150;
    const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
    if (fgRef) {
      // @ts-ignore tricky type deref here
      fgRef.current?.cameraPosition(
        { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }, // new position
        node, // lookAt ({ x, y, z })
        3000  // ms transition duration
      );
    }
  }, [fgRef]);

  if (!graphData) {
    return (
      <div className="graph-container">
        <div className="spinner-container">
          <div className="spinner">
            {loading ? <CircularProgress /> : "Upload your Tana JSON export file"}
          </div>
        </div>
      </div>
    );
  }
  else {
    // This code is a bit of a hack. We use the empty graph-container to get the dimensions of the container
    // and then pass those dimensions to the graph. This is necessary because the graph is rendered before the
    // container is sized, and we need to know the size of the container to render the graph.
    return (
      <div className="graph-container" ref={containerRef}>
        <div className="abs-container" >
          { twoDee ?
            <ForceGraph2D ref={fgRef}
              graphData={graphData}
              onNodeClick={handleNodeClick}
              onNodeDragEnd={node => {
                node.fx = node.x;
                node.fy = node.y;
                node.fz = node.z;
              }}
              linkColor={() => 'rgba(255,255,255,0.0)'}
              width={dimensions.width}
              height={dimensions.height}
            />
            : <ForceGraph3D ref={fgRef}
              graphData={graphData}
              onNodeClick={handleNodeClick}
              onNodeDragEnd={node => {
                node.fx = node.x;
                node.fy = node.y;
                node.fz = node.z;
              }}

              width={dimensions.width}
              height={dimensions.height}
            />
          }
        </div>
      </div>
    );
  }
}