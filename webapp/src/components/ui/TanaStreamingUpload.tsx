import React, { useCallback, useEffect } from 'react';
import { Input } from './input';
import { Upload, Loader2, X } from 'lucide-react';
import { Button } from './button';
import { useUploadMachine, useUploadActions } from '../../hooks/useAppStore';

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
  const uploadMachine = useUploadMachine();
  const {
    selectFile,
    startUpload,
    updateUploadProgress,
    cancelUpload,
    completeUpload,
    errorUpload,
  } = useUploadActions();

  const { state, context } = uploadMachine;
  const { file, abortController, ragProgress, lastError } = context;

  // Handle file selection
  const handleFileUpload = useCallback((event: React.FormEvent<HTMLInputElement>) => {
    const target = event.currentTarget;
    const selectedFile = target.files?.[0];
    if (selectedFile) {
      console.log('File selected:', selectedFile.name, selectedFile.size, selectedFile.type);
      selectFile(selectedFile);
    }
    event.currentTarget.value = '';
  }, [selectFile]);

  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const droppedFile = event.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/json') {
      console.log('File dropped:', droppedFile.name, droppedFile.size);
      selectFile(droppedFile);
    }
  }, [selectFile]);

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  }, []);

  const handleDragLeave = useCallback(() => {
    // Handle drag leave if needed
  }, []);

  // Auto-start upload when file is selected
  useEffect(() => {
    if (state === 'fileSelected' && file) {
      startUpload();
    }
  }, [state, file, startUpload]);

  // Main upload function with streaming
  const performUpload = useCallback(async () => {
    if (!file || !abortController || state !== 'uploading') return;

    console.log(`Starting streaming upload to ${endpoint}/stream...`);

    try {
      // Read file as JSON
      const reader = new FileReader();

      const uploadPromise = new Promise((resolve, reject) => {
        reader.onload = async (event) => {
          try {
            const fileContent = event.target?.result as string;
            const jsonData = JSON.parse(fileContent);

            console.log('File parsed successfully, starting streaming upload...');

            // Start the streaming upload with abort signal
            const response = await fetch(`${endpoint}/stream`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(jsonData),
              signal: abortController.signal,
            });

            if (!response.ok) {
              throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            if (!response.body) {
              throw new Error('No response stream available');
            }

            const streamReader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
              // Check if upload was cancelled
              if (abortController.signal.aborted) {
                console.log('Stream reading aborted by user');
                await streamReader.cancel();
                throw new DOMException('Aborted', 'AbortError');
              }

              const { done, value } = await streamReader.read();
              if (done) break;

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split('\n');

              // Keep incomplete line in buffer
              buffer = lines.pop() || '';

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  // Check for cancellation during data processing
                  if (abortController.signal.aborted) {
                    console.log('Stream processing aborted during data handling');
                    await streamReader.cancel();
                    throw new DOMException('Aborted', 'AbortError');
                  }

                  try {
                    const data = JSON.parse(line.slice(6));
                    console.log('Progress update:', data);

                    // Convert SSE data to progress updates
                    switch (data.type) {
                      case 'init':
                        updateUploadProgress({
                          phase: 'batch_processing',
                          totalTopics: data.total_topics,
                          totalNodes: data.total_nodes,
                          currentTopic: 0,
                          currentNode: 0,
                          percentage: 0,
                          skippedTopics: data.skipped_topics,
                          changedTopics: data.changed_topics,
                          deletedNodes: data.deleted_nodes,
                          // Track phase start time
                          phaseStartTimes: {
                            batch_processing: Date.now() / 1000,
                          },
                          // Initialize collection phase
                          collection: {
                            current: 0,
                            total: data.total_nodes,
                            completed: false,
                          },
                        });
                        break;

                      case 'batch_start':
                        updateUploadProgress({
                          phase: 'embedding',
                          totalNodes: data.total_nodes,
                          currentNode: 0,
                          totalBatches: data.estimated_batches,
                          currentBatch: 0,
                          elapsedSeconds: data.elapsed_seconds,
                          // Track phase start time for embedding and complete batch_processing
                          phaseStartTimes: {
                            ...context.ragProgress.phaseStartTimes,
                            embedding: Date.now() / 1000, // Convert to seconds
                          },
                          phaseCompletedTimes: {
                            ...context.ragProgress.phaseCompletedTimes,
                            ...(context.ragProgress.phaseStartTimes?.batch_processing && {
                              batch_processing: (Date.now() / 1000) - context.ragProgress.phaseStartTimes.batch_processing
                            }),
                          },
                          // Complete collection phase
                          collection: {
                            current: data.total_nodes,
                            total: data.total_nodes,
                            completed: true,
                          },
                          // Initialize embedding phase
                          embedding: {
                            current: 0,
                            total: data.total_nodes,
                            batch: 0,
                            totalBatches: data.estimated_batches,
                            completed: false,
                          },
                        });
                        break;

                      case 'embedding_progress':
                        updateUploadProgress({
                          phase: 'embedding',
                          currentNode: data.current_node,
                          totalNodes: data.total_nodes,
                          currentBatch: data.current_batch,
                          totalBatches: data.total_batches,
                          elapsedSeconds: data.elapsed_seconds,
                          etaSeconds: data.eta_seconds,
                          processingRate: data.processing_rate,
                          failedNodes: data.failed_nodes,
                          // Update embedding phase
                          embedding: {
                            current: data.current_node,
                            total: data.total_nodes,
                            batch: data.current_batch,
                            totalBatches: data.total_batches,
                            completed: false,
                          },
                        });
                        break;

                      case 'upsert_start':
                        updateUploadProgress({
                          phase: 'storing',
                          totalNodes: data.total_nodes,
                          currentNode: 0,
                          currentBatch: 0,
                          totalBatches: 0,
                          elapsedSeconds: data.elapsed_seconds,
                          // Track phase start time for storing and complete embedding
                          phaseStartTimes: {
                            ...context.ragProgress.phaseStartTimes,
                            storing: Date.now() / 1000,
                          },
                          phaseCompletedTimes: {
                            ...context.ragProgress.phaseCompletedTimes,
                            ...(context.ragProgress.phaseStartTimes?.embedding && {
                              embedding: (Date.now() / 1000) - context.ragProgress.phaseStartTimes.embedding
                            }),
                          },
                          // Complete embedding phase
                          embedding: {
                            current: data.total_nodes,
                            total: data.total_nodes,
                            batch: 0, // Will be updated from previous state
                            totalBatches: 0, // Will be updated from previous state
                            completed: true,
                          },
                          // Initialize storage phase
                          storage: {
                            current: 0,
                            total: data.total_nodes,
                            batch: 0,
                            totalBatches: 0,
                            completed: false,
                          },
                        });
                        break;

                      case 'storing_progress':
                        updateUploadProgress({
                          phase: 'storing',
                          currentNode: data.current_node,
                          totalNodes: data.total_nodes,
                          currentBatch: data.current_batch,
                          totalBatches: data.total_batches,
                          elapsedSeconds: data.elapsed_seconds,
                          failedNodes: data.failed_nodes,
                          // Update storage phase
                          storage: {
                            current: data.current_node,
                            total: data.total_nodes,
                            batch: data.current_batch,
                            totalBatches: data.total_batches,
                            completed: false,
                          },
                        });
                        break;

                      case 'complete':
                        // Complete upload with final progress data including completion times
                        completeUpload({
                          total_topics: data.total_topics,
                          total_nodes: data.total_nodes,
                          failed_nodes: data.failed_nodes,
                          // Include final progress state
                          finalProgress: {
                            phase: 'complete',
                            // Store completion time for storing phase
                            phaseCompletedTimes: {
                              ...context.ragProgress.phaseCompletedTimes,
                              ...(context.ragProgress.phaseStartTimes?.storing && {
                                storing: (Date.now() / 1000) - context.ragProgress.phaseStartTimes.storing
                              }),
                            },
                            storage: {
                              current: data.total_nodes,
                              total: data.total_nodes,
                              batch: 0, // Final batch count from previous state
                              totalBatches: 0, // Final total batches from previous state  
                              completed: true,
                            },
                          },
                        });
                        onSuccess({
                          total_topics: data.total_topics,
                          total_nodes: data.total_nodes,
                          failed_nodes: data.failed_nodes,
                        });
                        return;

                      case 'deletion_start':
                        updateUploadProgress({
                          phase: 'deletion',
                          totalNodesToDelete: data.total_nodes_to_delete,
                          deletedNodes: 0,
                          elapsedSeconds: data.elapsed_seconds,
                          // Track phase start time
                          phaseStartTimes: {
                            ...context.ragProgress.phaseStartTimes,
                            deletion: Date.now() / 1000,
                          },
                        });
                        break;

                      case 'deletion_progress':
                        updateUploadProgress({
                          phase: 'deletion',
                          deletedNodes: data.deleted_nodes,
                          totalNodesToDelete: data.total_nodes_to_delete,
                          elapsedSeconds: data.elapsed_seconds,
                        });
                        break;

                      case 'deletion_complete':
                        updateUploadProgress({
                          phase: 'deletion_complete',
                          deletedNodes: data.deleted_nodes,
                          totalNodesToDelete: data.total_nodes_to_delete,
                          elapsedSeconds: data.elapsed_seconds,
                          // Store completion time for deletion phase
                          phaseCompletedTimes: {
                            ...context.ragProgress.phaseCompletedTimes,
                            ...(context.ragProgress.phaseStartTimes?.deletion && {
                              deletion: (Date.now() / 1000) - context.ragProgress.phaseStartTimes.deletion
                            }),
                          },
                        });
                        break;

                      case 'error':
                        let errorMessage = data.message;
                        if (data.help) {
                          errorMessage += `\n\nSuggestion: ${data.help}`;
                        }
                        errorUpload(errorMessage);
                        onError(errorMessage);
                        return;

                      default:
                        // Handle other progress types as needed
                        console.log('Unhandled progress event type:', data.type, data);
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

      reader.readAsText(file);
      await uploadPromise;
    } catch (error: any) {
      console.error('Upload failed:', error);

      // Handle abort specifically
      if (error.name === 'AbortError') {
        console.log('Upload was aborted by user');
        // State machine will handle the cancellation
      } else {
        const errorMessage = error.message || 'Upload failed';
        errorUpload(errorMessage);
        onError(errorMessage);
      }
    }
  }, [
    file,
    abortController,
    state,
    endpoint,
    updateUploadProgress,
    completeUpload,
    errorUpload,
    onSuccess,
    onError,
  ]);

  // Start upload when state transitions to 'uploading'
  useEffect(() => {
    if (state === 'uploading') {
      performUpload();
    }
  }, [state, performUpload]);

  // Determine UI state
  const isUploading = state === 'uploading';
  const isProcessing = state === 'processing';
  const isCancelling = state === 'cancelling';
  const isCompleted = state === 'completed';
  const isError = state === 'error';
  const showProgress = isUploading || isProcessing || isCancelling;

  return (
    <div className="space-y-4">
      {/* File Drop Zone */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-4 text-center transition-colors ${'border-muted-foreground/25 hover:border-muted-foreground/50'
          } ${disabled || showProgress ? 'opacity-50 pointer-events-none' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        {isUploading ? (
          <div className="flex items-center justify-center space-x-2">
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            <span className="text-sm text-muted-foreground">Starting...</span>
          </div>
        ) : showProgress ? (
          <div className="flex flex-col items-center justify-center space-y-2">
            <div className="text-sm text-muted-foreground">Upload in progress...</div>
            <div className="text-xs text-muted-foreground">Use cancel button to stop</div>
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
          disabled={disabled || showProgress}
          className="hidden"
          id="tana-streaming-upload"
        />
        <label htmlFor="tana-streaming-upload" className="cursor-pointer absolute inset-0" />
      </div>

      {/* Controls */}
      {showProgress && (
        <div className="space-y-3">
          {/* Cancel Button - prominently displayed during processing */}
          {(isUploading || isProcessing) && !isCancelling ? (
            <div className="flex justify-center">
              <Button
                variant="outline"
                size="default"
                onClick={cancelUpload}
                className="w-full text-destructive hover:text-destructive hover:bg-destructive/10"
              >
                <X className="h-4 w-4 mr-2" />
                Cancel Upload
              </Button>
            </div>
          ) : isCancelling ? (
            <div className="text-center p-3 bg-muted/50 rounded-lg border">
              <div className="text-sm font-medium">⏹️ Cancelling...</div>
            </div>
          ) : null}
        </div>
      )}

      {/* Status Display for Completed/Error States */}
      {(isCompleted || isError) && (
        <div className="text-center p-3 bg-muted/50 rounded-lg border">
          <div className="text-sm font-medium">
            {isCompleted ? '✅ Upload Complete' : '❌ Upload Failed'}
          </div>
          {isCompleted && (
            <div className="text-xs text-muted-foreground mt-1">
              Drop a new file to start again
            </div>
          )}
          {isError && lastError && (
            <div className="text-xs text-destructive mt-1">{lastError}</div>
          )}
        </div>
      )}
    </div>
  );
} 