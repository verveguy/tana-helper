import React, { useContext, useEffect, useState } from "react";

import axios from 'axios';
import { VisualizerContext } from "./VisualizerContext";
import { Box, Button, Divider } from "@mui/material";


export default function ClassDiagramControls() {
  const { mermaidText, setMermaidText, loading, setLoading } = useContext(VisualizerContext)
  const [dumpFile, setDumpFile] = useState<File>();
  const [upload, setUpload] = useState(false);
  const [needsUpload, setNeedsUpload] = useState(true);

  const handleFileUpload = (event: React.FormEvent<HTMLInputElement>) => {
    const target = event.currentTarget;
    const file = target.files?.[0];
    setDumpFile(file);
    setNeedsUpload(false)
    setUpload(true);
    // reset input field so we can upload another file later
    event.currentTarget.value = "";
  };

  useEffect(() => {
    if (upload) {
      setLoading(true);
      axios.post('/mermaid_classes', dumpFile, {
        headers: {
          "Content-Type": "application/json",
        }
      })
        .then(response => {
          setMermaidText(response.data);
        })
        .catch(error => {
          console.error(error);
        })
        .finally(() => {
          setLoading(false);
          setUpload(false);
        })
    }
  }, [upload]);

  return (
    <div>
      <Divider />
      <Box style={{ padding: 10, marginLeft: 'auto', marginRight: 'auto' }}>
        <input hidden
          id="raised-button-file"
          accept="application/json"
          style={{ display: 'none' }}
          type="file"
          onChange={handleFileUpload}
        />
        <label htmlFor="raised-button-file">
          <Button component="span">
            Upload
          </Button>
        </label>
      </Box>
    </div>
  )
}
