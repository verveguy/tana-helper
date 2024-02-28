/*

  Visualize a Tana workspace tags as a class diagram.

*/

import { CircularProgress } from '@mui/material';
import { useWindowSize } from "@react-hook/window-size";
import React, { useContext, useEffect } from "react";
import './ClassDiagram.css';
import { TanaHelperContext } from "../TanaHelperContext";
import { Mermaid } from "./Mermaid";

export default function ClassDiagram() {
  const { mermaidText, setMermaidText, loading, setLoading } = useContext(TanaHelperContext)
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
        if (!mermaidText) {
          return (
            <div className="spinner-container">
              <div className="spinner">
                {loading ? <CircularProgress /> : "Upload your Tana JSON export file"}
              </div>
            </div>
          );
        } else {
          return (
            <Mermaid diagram={mermaidText} id="mermaid" style={{ width: '100%', height: '100%' }} />
          )
        }
      })()}
    </div>
  );
}

