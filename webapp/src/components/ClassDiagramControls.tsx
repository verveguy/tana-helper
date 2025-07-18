import React, { useState } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Upload } from "lucide-react";
import axios from 'axios';
// Replace context with Zustand store
import { useAppActions } from "../hooks/useAppStore";

export default function ClassDiagramControls() {
  // Use Zustand actions instead of context
  const { setMermaidText, setLoading } = useAppActions();
  
  const [dumpFile, setDumpFile] = useState<File>();
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFileUpload = (event: React.FormEvent<HTMLInputElement>) => {
    const target = event.currentTarget;
    const file = target.files?.[0];
    if (file) {
      setDumpFile(file);
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
    const file = event.dataTransfer.files[0];
    if (file && file.type === 'application/json') {
      setDumpFile(file);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
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
    <Card>
      <CardHeader>
        <CardTitle>Class Diagram Generator</CardTitle>
        <CardDescription>
          Upload a Tana JSON export to generate a class diagram
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* File Drop Zone */}
        <div
          className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
            isDragOver
              ? 'border-primary bg-primary/10'
              : 'border-muted-foreground/25 hover:border-muted-foreground/50'
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          <Upload className="mx-auto h-8 w-8 text-muted-foreground mb-2" />
          <div className="text-sm text-muted-foreground mb-2">
            Drag and drop your JSON file here, or click to browse
          </div>
          <Input
            type="file"
            accept=".json"
            onChange={handleFileUpload}
            className="hidden"
            id="file-upload"
          />
          <label htmlFor="file-upload">
            <Button variant="outline" asChild>
              <span className="cursor-pointer">
                Choose File
              </span>
            </Button>
          </label>
        </div>

        {/* Selected File */}
        {dumpFile && (
          <div className="text-sm text-muted-foreground">
            Selected: <span className="font-medium">{dumpFile.name}</span>
          </div>
        )}

        {/* Generate Button */}
        <Button
          onClick={uploadFile}
          disabled={!dumpFile}
          className="w-full"
        >
          Generate Class Diagram
        </Button>
      </CardContent>
    </Card>
  );
}
