/*

  Visualize a Tana Workspace in #d

  Thanks to the amazing https://github.com/vasturiano/react-force-graph

*/


import React, { useCallback, useContext, useEffect, useRef, useState } from "react";
import { CircularProgress } from '@mui/material';
import { Container } from "@mui/system";
import { VisualizerContext } from "../VisualizerContext";
import ForceGraph3D from 'react-force-graph-3d';
import './Visualizer.css';
import useWindowSize from "./utils";

export default function Visualizer(props: any) {
  // const [open, setOpen] = useState(true);
  const { windowWidth, windowHeight } = useWindowSize();
  const containerRef = useRef();
  const [dimensions, setDimensions] = useState({
    width: 0,
    height: 0,
  });
  const { graphData, loading } = useContext(VisualizerContext)
  const fgRef = useRef();

  useEffect(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.offsetWidth,
        height: containerRef.current.offsetHeight,
      });
    }
  }, [containerRef, windowWidth, windowHeight]); // if any of these change...

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

  if (loading) {
    return (
      <div className="graph-container">

        <div className="spinner-container">
          <div className="spinner">
            <CircularProgress />
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
          <ForceGraph3D ref={fgRef}
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
        </div>
      </div>
    );
  }
}
