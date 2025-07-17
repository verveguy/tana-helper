import React, { useState } from "react";
import { Box, Button, TextField } from "@mui/material";
import axios from 'axios';
// Replace context with Zustand store
import { useAppActions } from "../hooks/useAppStore";

export default function ClassDiagramControls() {
  // Use Zustand actions instead of context
  const { setMermaidText, setLoading } = useAppActions();
  
  const [dumpFile, setDumpFile] = useState<File>();

  const handleFileUpload = (event: React.FormEvent<HTMLInputElement>) => {
    const target = event.currentTarget;
    const file = target.files?.[0];
    if (file) {
      setDumpFile(file);
    }
  };

  const uploadFile = async () => {
    if (!dumpFile) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', dumpFile);
      
      const response = await axios.post('/class_diagram', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setMermaidText(response.data);
    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box display="flex" flexDirection="column" gap={2} padding={2}>
      <TextField
        type="file"
        onChange={handleFileUpload}
        inputProps={{ accept: '.json' }}
        helperText="Upload a Tana JSON export file"
      />
      
      <Button
        variant="contained"
        color="primary"
        onClick={uploadFile}
        disabled={!dumpFile}
      >
        Generate Class Diagram
      </Button>
    </Box>
  );
}
