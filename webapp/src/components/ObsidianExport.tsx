/*

  Visualize a Tana workspace tags as a class diagram.

*/

import { CircularProgress, Typography } from '@mui/material';
import React, { useContext, useEffect } from "react";
import './RAGIndex.css';
import { TanaHelperContext } from "../TanaHelperContext";

export default function ObsidianExport() {
  const { obsidianExportData, loading } = useContext(TanaHelperContext)

  useEffect(() => {
    (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'scroll');

    return () => {
      (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'hidden');
    }

  }, []);

  return (
    <div className="obisidian-export-container">
      {(() => {
        if (!obsidianExportData) {
          return (
            <div className="spinner-container">
              <div className="spinner">
                {loading ? <CircularProgress /> : "Upload your Tana JSON export file"}
              </div>
            </div>
          );
        } else {
          const lines = obsidianExportData.split('\n');
          return lines.map((line) => {
            return (<Typography className="obsidianExport">
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

