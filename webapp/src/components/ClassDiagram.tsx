/*

  Visualize a Tana workspace tags as a class diagram.

*/

import { CircularProgress } from '@mui/material';
import { useWindowSize } from "@react-hook/window-size";
import React, { useContext, useEffect } from "react";
import './ClassDiagram.css';
import { VisualizerContext } from "../VisualizerContext";
import { Mermaid } from "./Mermaid";

export default function ClassDiagram() {
  const { mermaidText, setMermaidText, loading, setLoading } = useContext(VisualizerContext)
  const [width, height] = useWindowSize();

  useEffect(() => {
    (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'scroll');

    return () => {
      (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'hidden');
    }

  }, []);

  return (
    <div className="diagram-container">
      {(() => {
        if (loading) {
          return (
            <div className="spinner-container">
              <div className="spinner">
                <CircularProgress />
              </div>
            </div>
          );
        } else {
          return (
            // <TransformWrapper>
            //   <TransformComponent>
            <Mermaid diagram={mermaidText} id="mermaid" style={{ width: '100%', height: '100%' }} />
            //   </TransformComponent>
            // </TransformWrapper> 
          )
        }
      })()}
    </div>
  );
}

