import React, { useState, useCallback, useEffect } from 'react';
import { Input } from './input';
import { Upload, Loader2 } from 'lucide-react';
import axios from 'axios';

export interface TanaFileUploadProps {
  endpoint: string;
  uploadType: 'json' | 'formdata'; // Whether to send as JSON or FormData
  onSuccess: (data: any, rawFileData?: any) => void; // Add optional rawFileData parameter
  onError: (error: string) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

export default function TanaFileUpload({
  endpoint,
  uploadType,
  onSuccess,
  onError,
  loading,
  setLoading,
}: TanaFileUploadProps) {
  const [dumpFile, setDumpFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFileUpload = useCallback((event: React.FormEvent<HTMLInputElement>) => {
    const target = event.currentTarget;
    const file = target.files?.[0];
    if (file) {
      console.log('File selected:', file.name, file.size, file.type);
      setDumpFile(file);
    }
    event.currentTarget.value = '';
  }, []);

  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
    const file = event.dataTransfer.files[0];
    if (file && file.type === 'application/json') {
      console.log('File dropped:', file.name, file.size);
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

  // Commented out clearFile as it's not used
  // const clearFile = useCallback(() => {
  //   setDumpFile(null);
  // }, []);

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
          reader.onload = async event => {
            try {
              const fileContent = event.target?.result as string;
              const jsonData = JSON.parse(fileContent);
              rawFileData = jsonData; // Store the parsed JSON data
              console.log('File parsed successfully, sending to server...');

              const response = await axios.post(endpoint, jsonData, {
                headers: {
                  'Content-Type': 'application/json',
                },
              });
              resolve(response);
            } catch {
              reject(new Error('Invalid JSON file. Please check your file format.'));
            }
          };

          reader.onerror = () => {
            reject(new Error('Failed to read file. Please try again.'));
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

      console.log('Upload successful, response:', response);
      onSuccess(response.data, rawFileData); // Pass both response and raw data
      setDumpFile(null); // Clear file after successful upload
    } catch (error: any) {
      console.error('Upload failed:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Upload failed';
      onError(`Failed to process file: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  }, [dumpFile, uploadType, endpoint, setLoading, onSuccess, onError]);

  // Auto-upload when file is selected
  useEffect(() => {
    if (dumpFile && !loading) {
      uploadFile();
    }
  }, [dumpFile, loading, uploadFile]);

  return (
    <div className="relative">
      {/* Simplified File Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-4 text-center transition-colors ${
          isDragOver
            ? 'border-primary bg-primary/10'
            : 'border-muted-foreground/25 hover:border-muted-foreground/50'
        } ${loading ? 'opacity-50 pointer-events-none' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        {loading ? (
          <div className="flex items-center justify-center space-x-2">
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            <span className="text-sm text-muted-foreground">Processing...</span>
          </div>
        ) : (
          <>
            <Upload className="mx-auto h-6 w-6 text-muted-foreground mb-2" />
            <div className="text-sm text-muted-foreground">Drop file or click to browse</div>
          </>
        )}

        <Input
          type="file"
          accept=".json"
          onChange={handleFileUpload}
          disabled={loading}
          className="hidden"
          id="tana-file-upload"
        />
        <label htmlFor="tana-file-upload" className="cursor-pointer absolute inset-0" />
      </div>
    </div>
  );
}
