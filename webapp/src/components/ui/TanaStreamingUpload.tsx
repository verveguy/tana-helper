import React, { useState, useCallback, useEffect } from 'react';
import { Input } from './input';
import { Upload, Loader2, X } from 'lucide-react';
import { Button } from './button';
import ProgressDisplay from './ProgressDisplay';
import { useRagProgress, useAppActions } from '../../hooks/useAppStore';

export interface TanaStreamingUploadProps {
  endpoint: string; // Base endpoint, will append '/stream' for streaming
  onSuccess: (data: any) => void;
  onError: (error: string) => void;
  disabled?: boolean;
}

export default function TanaStreamingUpload({
  endpoint,
  onSuccess,
  onError,
  disabled = false,
}: TanaStreamingUploadProps) {
  const [dumpFile, setDumpFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const ragProgress = useRagProgress();
  const { updateRagProgress, resetRagProgress, setRagError } = useAppActions();

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

  const cancelUpload = useCallback(() => {
    setIsUploading(false);
    resetRagProgress();
    setDumpFile(null);
  }, [resetRagProgress]);

  const uploadFileWithProgress = useCallback(async () => {
    if (!dumpFile || isUploading) return;

    console.log(`Starting streaming upload to ${endpoint}/stream...`);
    setIsUploading(true);
    resetRagProgress();
    updateRagProgress({ isActive: true, phase: 'starting' });
    setRagError(null);

    try {
      // Read file as JSON
      const reader = new FileReader();

      const uploadPromise = new Promise((resolve, reject) => {
        reader.onload = async (event) => {
          try {
            const fileContent = event.target?.result as string;
            const jsonData = JSON.parse(fileContent);

            console.log('File parsed successfully, starting streaming upload...');

            // Start the streaming upload
            const response = await fetch(`${endpoint}/stream`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(jsonData),
            });

            if (!response.ok) {
              throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            if (!response.body) {
              throw new Error('No response stream available');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split('\n');

              // Keep incomplete line in buffer
              buffer = lines.pop() || '';

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    const data = JSON.parse(line.slice(6));
                    console.log('Progress update:', data);

                    switch (data.type) {
                      case 'init':
                        updateRagProgress({
                          phase: 'processing',
                          totalTopics: data.total_topics,
                          totalNodes: data.total_nodes,
                          currentTopic: 0,
                          currentNode: 0,
                          percentage: 0,
                        });
                        break;

                      case 'topic_start':
                        updateRagProgress({
                          currentTopic: data.current_topic,
                          totalTopics: data.total_topics,
                          currentNode: data.processed_nodes,
                          totalNodes: data.total_nodes,
                          percentage: data.percentage,
                          currentTopicName: data.topic_name,
                          currentTopicId: data.topic_id,
                          elapsedSeconds: data.elapsed_seconds,
                          etaSeconds: data.eta_seconds,
                          processingRate: data.processing_rate,
                        });
                        break;

                      case 'topic_complete':
                        updateRagProgress({
                          currentTopic: data.current_topic,
                          totalTopics: data.total_topics,
                          currentNode: data.processed_nodes,
                          totalNodes: data.total_nodes,
                          percentage: data.percentage,
                          elapsedSeconds: data.elapsed_seconds,
                          etaSeconds: data.eta_seconds,
                          processingRate: data.processing_rate,
                        });
                        break;

                      case 'node_progress':
                        updateRagProgress({
                          currentNode: data.processed_nodes,
                          totalNodes: data.total_nodes,
                          percentage: data.percentage,
                          topicNode: data.topic_node,
                          topicNodes: data.topic_nodes,
                          elapsedSeconds: data.elapsed_seconds,
                          etaSeconds: data.eta_seconds,
                          processingRate: data.processing_rate,
                        });
                        break;

                      case 'complete':
                        updateRagProgress({
                          phase: 'complete',
                          percentage: 100,
                          currentNode: data.total_nodes,
                          elapsedSeconds: data.elapsed_seconds,
                        });
                        onSuccess({
                          total_topics: data.total_topics,
                          total_nodes: data.total_nodes
                        });
                        setDumpFile(null);
                        setIsUploading(false);
                        break;

                      case 'topic_error':
                        console.warn('Topic error:', data.error);
                        // Continue processing, just log the error
                        break;

                      case 'keepalive':
                        // Just update elapsed time, no other action needed
                        if (data.elapsed_seconds) {
                          updateRagProgress({
                            elapsedSeconds: data.elapsed_seconds,
                          });
                        }
                        break;

                      case 'cancelled':
                        updateRagProgress({
                          phase: 'error',
                          error: 'Processing cancelled by user',
                        });
                        onError('Processing cancelled by user');
                        setIsUploading(false);
                        break;

                      case 'error':
                        updateRagProgress({
                          phase: 'error',
                          error: data.message,
                        });
                        onError(data.message);
                        setIsUploading(false);
                        break;
                    }
                  } catch (parseError) {
                    console.warn('Failed to parse progress data:', parseError, 'Line:', line);
                  }
                }
              }
            }

            resolve(true);
          } catch (error: any) {
            reject(error);
          }
        };

        reader.onerror = () => {
          reject(new Error('Failed to read file. Please try again.'));
        };
      });

      reader.readAsText(dumpFile);
      await uploadPromise;

    } catch (error: any) {
      console.error('Upload failed:', error);
      const errorMessage = error.message || 'Upload failed';
      updateRagProgress({
        phase: 'error',
        error: errorMessage,
      });
      onError(errorMessage);
      setIsUploading(false);
      setDumpFile(null);
    }
  }, [dumpFile, isUploading, endpoint, updateRagProgress, resetRagProgress, setRagError, onSuccess, onError]);

  // Auto-upload when file is selected (if not already uploading)
  useEffect(() => {
    if (dumpFile && !isUploading && ragProgress.phase === 'idle') {
      uploadFileWithProgress();
    }
  }, [dumpFile, isUploading, ragProgress.phase, uploadFileWithProgress]);

  const showProgress = ragProgress.isActive && ragProgress.phase !== 'idle';

  return (
    <div className="space-y-4">
      {/* File Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${isDragOver
          ? 'border-primary bg-primary/10'
          : 'border-muted-foreground/25 hover:border-muted-foreground/50'
          } ${disabled || isUploading ? 'opacity-50 pointer-events-none' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        {isUploading ? (
          <div className="flex items-center justify-center space-x-2">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <span className="text-sm text-muted-foreground">Starting upload...</span>
          </div>
        ) : (
          <>
            <Upload className="mx-auto h-8 w-8 text-muted-foreground mb-3" />
            <div className="text-lg font-medium mb-2">Drop your Tana export file here</div>
            <div className="text-sm text-muted-foreground mb-4">
              or click to browse for a JSON file
            </div>
            <Button variant="outline" size="sm" disabled={disabled}>
              Select File
            </Button>
          </>
        )}

        <Input
          type="file"
          accept=".json"
          onChange={handleFileUpload}
          disabled={disabled || isUploading}
          className="hidden"
          id="tana-streaming-upload"
        />
        <label
          htmlFor="tana-streaming-upload"
          className="cursor-pointer absolute inset-0"
        />
      </div>

      {/* Progress Display */}
      {showProgress && (
        <div className="space-y-3">
          <ProgressDisplay progress={ragProgress} />

          {/* Cancel Button */}
          {isUploading && ragProgress.phase === 'starting' && (
            <div className="flex justify-center">
              <Button
                variant="outline"
                size="sm"
                onClick={cancelUpload}
                className="text-destructive hover:text-destructive"
              >
                <X className="h-4 w-4 mr-2" />
                Cancel Upload
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
} 