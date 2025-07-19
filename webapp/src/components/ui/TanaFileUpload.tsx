import React, { useState, useCallback } from "react";
import { Button } from "./button";
import { Input } from "./input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./card";
import { Upload, Loader2, X } from "lucide-react";
import axios from 'axios';

export interface TanaFileUploadProps {
  title: string;
  description: string;
  buttonText: string;
  endpoint: string;
  uploadType: 'json' | 'formdata'; // Whether to send as JSON or FormData
  onSuccess: (data: any, rawFileData?: any) => void; // Add optional rawFileData parameter
  onError: (error: string) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

export default function TanaFileUpload({
  title,
  description,
  buttonText,
  endpoint,
  uploadType,
  onSuccess,
  onError,
  loading,
  setLoading
}: TanaFileUploadProps) {
  const [dumpFile, setDumpFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFileUpload = useCallback((event: React.FormEvent<HTMLInputElement>) => {
    const target = event.currentTarget;
    const file = target.files?.[0];
    if (file) {
      console.log("File selected:", file.name, file.size, file.type);
      setDumpFile(file);
    }
    event.currentTarget.value = "";
  }, []);

  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
    const file = event.dataTransfer.files[0];
    if (file && file.type === 'application/json') {
      console.log("File dropped:", file.name, file.size);
      setDumpFile(file);
    }
  }, []);

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const clearFile = useCallback(() => {
    setDumpFile(null);
  }, []);

  const uploadFile = useCallback(async () => {
    if (!dumpFile) return;

    console.log(`Starting ${uploadType} upload to ${endpoint}...`);
    setLoading(true);

    try {
      let response;
      let rawFileData: any = null;
      
      if (uploadType === 'json') {
        // Read file as JSON and send as application/json
        const reader = new FileReader();
        
        const uploadPromise = new Promise((resolve, reject) => {
          reader.onload = async (event) => {
            try {
              const fileContent = event.target?.result as string;
              const jsonData = JSON.parse(fileContent);
              rawFileData = jsonData; // Store the parsed JSON data
              console.log("File parsed successfully, sending to server...");
              
              const response = await axios.post(endpoint, jsonData, {
                headers: {
                  "Content-Type": "application/json",
                }
              });
              resolve(response);
            } catch (parseError) {
              reject(new Error("Invalid JSON file. Please check your file format."));
            }
          };
          
          reader.onerror = () => {
            reject(new Error("Failed to read file. Please try again."));
          };
        });
        
        reader.readAsText(dumpFile);
        response = await uploadPromise;
      } else {
        // Send as FormData (multipart/form-data)
        const formData = new FormData();
        formData.append('file', dumpFile);
        
        response = await axios.post(endpoint, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        // For FormData uploads, we can't easily get the raw data back
        // but we can store the file for potential re-upload
        rawFileData = dumpFile;
      }

      console.log("Upload successful, response:", response);
      onSuccess(response.data, rawFileData); // Pass both response and raw data
      
    } catch (error: any) {
      console.error("Upload failed:", error);
      const errorMessage = error.response?.data?.detail || error.message || 'Upload failed';
      onError(`Failed to process file: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  }, [dumpFile, uploadType, endpoint, setLoading, onSuccess, onError]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* File Drop Zone */}
        <div
          className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
            isDragOver
              ? 'border-primary bg-primary/10'
              : 'border-muted-foreground/25 hover:border-muted-foreground/50'
          } ${loading ? 'opacity-50 pointer-events-none' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          <Upload className="mx-auto h-8 w-8 text-muted-foreground mb-2" />
          <div className="text-sm text-muted-foreground mb-2">
            Drag and drop your Tana JSON file here, or click to browse
          </div>
          <Input
            type="file"
            accept=".json"
            onChange={handleFileUpload}
            disabled={loading}
            className="hidden"
            id="tana-file-upload"
          />
          <label htmlFor="tana-file-upload">
            <Button variant="outline" asChild disabled={loading}>
              <span className="cursor-pointer">
                Choose File
              </span>
            </Button>
          </label>
        </div>

        {/* Selected File */}
        {dumpFile && (
          <div className="flex items-center justify-between p-3 bg-muted/50 rounded-md">
            <div className="text-sm">
              <span className="text-muted-foreground">Selected: </span>
              <span className="font-medium">{dumpFile.name}</span>
              <span className="text-xs text-muted-foreground ml-2">
                ({(dumpFile.size / 1024 / 1024).toFixed(2)} MB)
              </span>
            </div>
            {!loading && (
              <Button variant="ghost" size="sm" onClick={clearFile}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        )}

        {/* Loading Progress Indicator */}
        {loading && (
          <div className="border border-border rounded-lg p-4 bg-muted/50">
            <div className="flex items-center space-x-3">
              <Loader2 className="h-5 w-5 animate-spin text-primary flex-shrink-0" />
              <div className="flex-1 space-y-1">
                <div className="text-sm font-medium text-foreground">
                  Processing File
                </div>
                <div className="text-xs text-muted-foreground">
                  {uploadType === 'json' ? 'Parsing JSON and building structure...' : 'Uploading file and processing...'}
                </div>
              </div>
            </div>
            <div className="mt-3 w-full bg-border rounded-full h-1.5">
              <div className="bg-primary h-1.5 rounded-full animate-pulse" style={{width: '60%'}}></div>
            </div>
          </div>
        )}

        {/* Upload Button */}
        <Button
          onClick={uploadFile}
          disabled={!dumpFile || loading}
          className="w-full"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            buttonText
          )}
        </Button>
      </CardContent>
    </Card>
  );
} 