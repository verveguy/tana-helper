/*

  Visualize a Tana workspace tags as a class diagram.

*/

import { CircularProgress, Typography } from '@mui/material';
import React, { useContext, useEffect } from "react";
import './RAGIndex.css';
import { TanaHelperContext } from "../TanaHelperContext";

export default function RAGIndex() {
  const { ragIndexData, loading } = useContext(TanaHelperContext)

  useEffect(() => {
    (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'scroll');

    return () => {
      (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'hidden');
    }

  }, []);

  return (
    <div className="ragindex-container">
      {(() => {
        if (!ragIndexData) {
          return (
            <div className="spinner-container">
              <div className="spinner">
                {loading ? <CircularProgress /> : "Upload your Tana JSON export file"}
              </div>
            </div>
          );
        } else {
          const lines = ragIndexData.split('\n');
          return lines.map((line) => {
            return (<Typography className="ragindex">
              {line}
            </Typography>
            )
          }
          );
        }
      })()}
    </div>
  );
}

