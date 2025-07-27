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

// 🎯 RELIABLE: Progress event handler with validation and error recovery
interface ProgressEventData {
  type: string;
  [key: string]: any;
}

function validateProgressEvent(data: ProgressEventData): boolean {
  if (!data || typeof data !== 'object' || !data.type) {
    return false;
  }

  // Basic validation for different event types
  switch (data.type) {
    case 'init':
      return typeof data.total_topics === 'number' && typeof data.total_nodes === 'number';
    case 'batch_start':
    case 'embedding_progress':
    case 'storing_progress':
      return typeof data.total_nodes === 'number';
    case 'complete':
      return typeof data.total_topics === 'number' && typeof data.total_nodes === 'number';
    case 'error':
      return typeof data.message === 'string';
    case 'deletion_start':
    case 'deletion_progress':
    case 'deletion_complete':
      return (
        typeof data.total_nodes_to_delete === 'number' || typeof data.deleted_nodes === 'number'
      );
    default:
      return true; // Allow unknown event types to pass through
  }
}

function createProgressUpdate(eventData: ProgressEventData, currentProgress: any): any {
  // Note: Phase timing is now handled client-side within individual PhaseItem components

  // 🎯 RELIABLE: Simplified event processing with consistent patterns
  switch (eventData.type) {
    case 'phase_skipped':
      // Handle phases that are skipped by the backend (e.g., no nodes to embed/store)
      return {
        skippedPhases: {
          ...currentProgress.skippedPhases,
          [eventData.phase]: {
            skipped: true,
            reason: eventData.reason || 'No work needed',
          },
        },
        // Don't change the current phase - let natural progression continue
      };

    case 'collection_start':
      return {
        phase: 'batch_processing',
        totalTopics: eventData.total_topics,
        currentTopic: 0,
        collection: {
          current: 0,
          total: eventData.total_topics,
          completed: false,
        },
      };

    case 'collection_progress':
      return {
        phase: 'batch_processing',
        totalTopics: eventData.total_topics,
        currentTopic: eventData.current_topic,
        totalNodes: eventData.current_nodes,
        collection: {
          current: eventData.current_topic,
          total: eventData.total_topics,
          completed: false,
        },
      };

    case 'collection_complete':
      return {
        phase: 'batch_processing',
        totalTopics: eventData.total_topics,
        totalNodes: eventData.total_nodes,
        currentTopic: eventData.total_topics,
        collection: {
          current: eventData.total_topics,
          total: eventData.total_topics,
          completed: true,
        },
      };

    case 'init':
      return {
        phase: 'batch_processing',
        totalTopics: eventData.total_topics,
        totalNodes: eventData.total_nodes,
        currentTopic: 0,
        currentNode: 0,
        percentage: 0,
        skippedTopics: eventData.skipped_topics || 0,
        changedTopics: eventData.changed_topics || 0,
        deletedNodes: eventData.deleted_nodes || 0,

        collection: {
          current: 0,
          total: eventData.total_nodes,
          completed: false,
        },
      };

    case 'batch_start':
      return {
        phase: 'embedding',
        totalNodes: eventData.total_nodes,
        currentNode: 0,
        totalBatches: eventData.estimated_batches || 0,
        currentBatch: 0,
        elapsedSeconds: eventData.elapsed_seconds,

        collection: {
          current: eventData.total_nodes,
          total: eventData.total_nodes,
          completed: true,
        },
        embedding: {
          current: 0,
          total: eventData.total_nodes,
          batch: 0,
          totalBatches: eventData.estimated_batches || 0,
          completed: false,
        },
      };

    case 'embedding_progress':
      return {
        phase: 'embedding',
        currentNode: eventData.current_node || 0,
        totalNodes: eventData.total_nodes,
        currentBatch: eventData.current_batch || 0,
        totalBatches: eventData.total_batches || 0,
        elapsedSeconds: eventData.elapsed_seconds,
        etaSeconds: eventData.eta_seconds,
        processingRate: eventData.processing_rate,
        failedNodes: eventData.failed_nodes || 0,
        embedding: {
          current: eventData.current_node || 0,
          total: eventData.total_nodes,
          batch: eventData.current_batch || 0,
          totalBatches: eventData.total_batches || 0,
          completed: false,
        },
      };

    case 'upsert_start':
      return {
        phase: 'storing',
        totalNodes: eventData.total_nodes,
        currentNode: 0,
        currentBatch: 0,
        totalBatches: 0,
        elapsedSeconds: eventData.elapsed_seconds,

        embedding: {
          ...currentProgress.embedding,
          current: eventData.total_nodes,
          completed: true,
        },
        storage: {
          current: 0,
          total: eventData.total_nodes,
          batch: 0,
          totalBatches: 0,
          completed: false,
        },
      };

    case 'storing_progress':
      return {
        phase: 'storing',
        currentNode: eventData.current_node || 0,
        totalNodes: eventData.total_nodes,
        currentBatch: eventData.current_batch || 0,
        totalBatches: eventData.total_batches || 0,
        elapsedSeconds: eventData.elapsed_seconds,
        failedNodes: eventData.failed_nodes || 0,
        storage: {
          current: eventData.current_node || 0,
          total: eventData.total_nodes,
          batch: eventData.current_batch || 0,
          totalBatches: eventData.total_batches || 0,
          completed: false,
        },
      };

    case 'deletion_start':
      return {
        phase: 'deletion',
        totalNodesToDelete: eventData.total_nodes_to_delete,
        deletedNodes: 0,
        elapsedSeconds: eventData.elapsed_seconds,
      };

    case 'deletion_progress':
      return {
        phase: 'deletion',
        deletedNodes: eventData.deleted_nodes || 0,
        totalNodesToDelete: eventData.total_nodes_to_delete,
        elapsedSeconds: eventData.elapsed_seconds,
      };

    case 'deletion_complete':
      return {
        phase: 'deletion_complete',
        deletedNodes: eventData.deleted_nodes || 0,
        totalNodesToDelete: eventData.total_nodes_to_delete,
        elapsedSeconds: eventData.elapsed_seconds,
      };

    case 'complete':
      return {
        phase: 'complete',
        isActive: false,
        totalTopics: eventData.total_topics,
        totalNodes: eventData.total_nodes,
        failedNodes: eventData.failed_nodes || 0,
        elapsedSeconds: eventData.elapsed_seconds,
        // Complete all phases
        storage: {
          ...currentProgress.storage,
          current: eventData.total_nodes,
          completed: true,
        },
      };

    default:
      console.warn('Unknown progress event type:', eventData.type);
      return {}; // Return empty update for unknown events
  }
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

  // 🎯 SIMPLIFIED: Direct progress updates without timeout detection
  // Since RAG operations provide frequent batch updates (~1 second intervals),
  // timeout detection is unnecessary and can cause false positives
  const trackProgressUpdate = React.useCallback(
    (progressUpdate: any) => {
      // Clear any stuck state flags that might be present
      if (progressUpdate.isStuck) {
        delete progressUpdate.isStuck;
        delete progressUpdate.timeoutWarning;
      }

      updateUploadProgress(progressUpdate);
    },
    [updateUploadProgress]
  );

  // Handle file selection
  const handleFileUpload = useCallback(
    (event: React.FormEvent<HTMLInputElement>) => {
      const target = event.currentTarget;
      const selectedFile = target.files?.[0];
      if (selectedFile) {
        console.log('File selected:', selectedFile.name, selectedFile.size, selectedFile.type);
        selectFile(selectedFile);
      }
      event.currentTarget.value = '';
    },
    [selectFile]
  );

  const handleDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      const droppedFile = event.dataTransfer.files[0];
      if (droppedFile && droppedFile.type === 'application/json') {
        console.log('File dropped:', droppedFile.name, droppedFile.size);
        selectFile(droppedFile);
      }
    },
    [selectFile]
  );

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

  // Note: No timeout tracking needed since RAG operations provide frequent updates

  // Main upload function with streaming
  const performUpload = useCallback(async () => {
    if (!file || !abortController || state !== 'uploading') return;

    console.log(`Starting streaming upload to ${endpoint}/stream...`);

    try {
      // Read file as JSON
      const reader = new FileReader();

      const uploadPromise = new Promise((resolve, reject) => {
        reader.onload = async event => {
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

                    // 🎯 RELIABLE: Validate event before processing
                    if (!validateProgressEvent(data)) {
                      console.warn('Invalid progress event received:', data);
                      continue; // Skip invalid events
                    }

                    console.log('Valid progress update:', data);

                    // 🎯 RELIABLE: Use centralized progress update creation
                    const progressUpdate = createProgressUpdate(data, ragProgress);
                    if (Object.keys(progressUpdate).length > 0) {
                      trackProgressUpdate(progressUpdate);
                    }

                    // 🎯 RELIABLE: Handle only terminal events in switch
                    switch (data.type) {
                      case 'complete':
                        // Complete upload - progress update is already handled above by createProgressUpdate
                        // Only complete if not already completed (prevent duplicate completion)
                        if (uploadMachine.state !== 'completed') {
                          completeUpload({
                            total_topics: data.total_topics,
                            total_nodes: data.total_nodes,
                            failed_nodes: data.failed_nodes,
                          });
                          onSuccess({
                            total_topics: data.total_topics,
                            total_nodes: data.total_nodes,
                            failed_nodes: data.failed_nodes,
                          });
                        }
                        return;

                      case 'error':
                        let errorMessage = data.message;
                        if (data.help) {
                          errorMessage += `\n\nSuggestion: ${data.help}`;
                        }
                        errorUpload(errorMessage);
                        onError(errorMessage);
                        return;

                      default:
                        // All other progress events (init, batch_start, embedding_progress, etc.)
                        // are handled by createProgressUpdate above - no action needed here
                        break;
                    }
                  } catch (parseError) {
                    // 🎯 RELIABLE: Better error handling for progress events
                    console.warn('Failed to parse progress event:', {
                      error: parseError,
                      line: line.substring(0, 100), // Truncate long lines
                      lineLength: line.length,
                    });

                    // Don't fail the entire upload for a single bad progress event
                    // The upload can continue and show progress when valid events arrive
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

      // 🎯 RECOVERY: Better error categorization and recovery advice
      if (error.name === 'AbortError') {
        console.log('Upload was aborted by user');
        // State machine will handle the cancellation
        return;
      }

      // 🎯 RECOVERY: Provide specific error messages and recovery suggestions
      let errorMessage = 'Upload failed';
      let suggestion = '';

      if (error.message?.includes('fetch')) {
        errorMessage = 'Network connection failed';
        suggestion = 'Please check your internet connection and try again.';
      } else if (error.message?.includes('timeout') || error.message?.includes('timed out')) {
        errorMessage = 'Upload timed out';
        suggestion = 'The server may be busy. Please wait a moment and try again.';
      } else if (error.message?.includes('413') || error.message?.includes('too large')) {
        errorMessage = 'File too large';
        suggestion =
          'Your Tana export file is too large. Try exporting a smaller subset of your data.';
      } else if (error.message?.includes('401') || error.message?.includes('unauthorized')) {
        errorMessage = 'Authentication failed';
        suggestion = 'Please check your API configuration and try again.';
      } else if (error.message?.includes('500') || error.message?.includes('server error')) {
        errorMessage = 'Server error';
        suggestion = 'The server encountered an error. Please try again in a few minutes.';
      } else if (error.message) {
        errorMessage = error.message;
        suggestion = 'Please try again. If the problem persists, check your configuration.';
      }

      const fullErrorMessage = suggestion
        ? `${errorMessage}\n\nSuggestion: ${suggestion}`
        : errorMessage;

      errorUpload(fullErrorMessage);
      onError(fullErrorMessage);
    }
  }, [
    file,
    abortController,
    state,
    endpoint,
    updateUploadProgress, // 🎯 CONSOLIDATED: Single dependency
    completeUpload,
    errorUpload,
    onSuccess,
    onError,
    ragProgress, // Added ragProgress to dependencies
  ]);

  // Start upload when state transitions to 'uploading'
  useEffect(() => {
    if (state === 'uploading') {
      performUpload();
    }
  }, [state, performUpload]);

  // 🎯 SIMPLIFIED: Derive UI state from state machine
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
        className={`relative border-2 border-dashed rounded-lg p-4 text-center transition-colors ${'border-muted-foreground/25 hover:border-muted-foreground/50'} ${disabled || showProgress ? 'opacity-50 pointer-events-none' : ''}`}
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
            <div className="text-xs text-muted-foreground mt-1">Drop a new file to start again</div>
          )}
          {isError && lastError && (
            <div className="space-y-3 mt-2">
              <div className="text-xs text-destructive whitespace-pre-wrap">{lastError}</div>
              {/* 🎯 RECOVERY: Manual retry button for failed uploads */}
              <div className="flex flex-col space-y-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    // Retry the upload with the same file
                    if (file) {
                      startUpload();
                    }
                  }}
                  className="text-blue-600 hover:text-blue-700 border-blue-300 hover:border-blue-400"
                >
                  🔄 Retry Upload
                </Button>
                <div className="text-xs text-muted-foreground">
                  Or drop a new file to start fresh
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
