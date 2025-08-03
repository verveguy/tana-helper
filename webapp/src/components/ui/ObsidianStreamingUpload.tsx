// React import not needed for JSX in React 17+
import React, { useCallback, useEffect } from 'react';
import { Upload, X, FileText } from 'lucide-react';
import { Button } from './button';

// Replace context with Zustand store
import { useUploadMachine, useUploadActions } from '../../hooks/useAppStore';

export interface ObsidianStreamingUploadProps {
  endpoint: string; // Base endpoint, will append '/stream' for streaming
  onSuccess: (data: any) => void;
  onError: (error: string) => void;
  disabled?: boolean;
}

interface ObsidianProgressEventData {
  type: string;
  [key: string]: any;
}

function validateObsidianProgressEvent(data: ObsidianProgressEventData): boolean {
  // Basic validation for Obsidian progress events
  return (
    data &&
    typeof data === 'object' &&
    typeof data.type === 'string' &&
    ['starting', 'processing', 'complete'].includes(data.type)
  );
}

function createObsidianProgressUpdate(
  eventData: ObsidianProgressEventData,
  currentProgress: any
): any {
  switch (eventData.type) {
    case 'starting':
      return {
        isActive: true,
        phase: 'starting',
        totalTopics: eventData.total_topics,
        currentTopic: 0,
        percentage: 0,
        currentTopicName: undefined,
        currentTopicId: undefined,
      };

    case 'processing':
      return {
        isActive: true,
        phase: 'processing',
        totalTopics: eventData.total_topics,
        currentTopic: eventData.current_topic,
        percentage: eventData.percentage,
        currentTopicName: eventData.current_topic_name,
        currentTopicId: eventData.current_topic_id,
      };

    case 'complete':
      return {
        isActive: false,
        phase: 'complete',
        totalTopics: eventData.total_topics,
        currentTopic: eventData.total_topics,
        percentage: 100,
        vaultPath: eventData.vault_path,
      };

    default:
      console.warn('Unknown Obsidian progress event type:', eventData.type);
      return {}; // Return empty update for unknown events
  }
}

export default function ObsidianStreamingUpload({
  endpoint,
  onSuccess,
  onError,
  disabled = false,
}: ObsidianStreamingUploadProps) {
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
  const { file, abortController, obsidianProgress, lastError } = context;

  // Track Obsidian progress updates
  const trackProgressUpdate = React.useCallback(
    (progressUpdate: any) => {
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

  // Auto-start upload when file is selected
  useEffect(() => {
    if (state === 'fileSelected' && file) {
      startUpload();
    }
  }, [state, file, startUpload]);

  // Main upload function with streaming
  const performUpload = useCallback(async () => {
    if (!file || !abortController || state !== 'uploading') return;

    console.log(`Starting Obsidian streaming upload to ${endpoint}/stream...`);

    try {
      // Read file as JSON
      const reader = new FileReader();

      const uploadPromise = new Promise((resolve, reject) => {
        reader.onload = async event => {
          try {
            const fileContent = event.target?.result as string;
            const jsonData = JSON.parse(fileContent);

            console.log('File parsed successfully, starting Obsidian streaming upload...');

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

                    // Validate event before processing
                    if (!validateObsidianProgressEvent(data)) {
                      console.warn('Invalid Obsidian progress event received:', data);
                      continue; // Skip invalid events
                    }

                    console.log('Valid Obsidian progress update:', data);

                    // Create progress update for Obsidian events
                    const progressUpdate = createObsidianProgressUpdate(data, obsidianProgress);
                    if (Object.keys(progressUpdate).length > 0) {
                      trackProgressUpdate(progressUpdate);
                    }

                    // Handle terminal events
                    switch (data.type) {
                      case 'complete':
                        // Complete upload
                        completeUpload({
                          total_topics: data.total_topics,
                          vault_path: data.vault_path,
                        });
                        onSuccess({
                          total_topics: data.total_topics,
                          vault_path: data.vault_path,
                        });
                        resolve(data);
                        return;

                      case 'error':
                        const errorMessage = data.error || 'Unknown error during Obsidian export';
                        errorUpload(errorMessage);
                        onError(errorMessage);
                        reject(new Error(errorMessage));
                        return;
                    }
                  } catch (parseError) {
                    console.warn('Failed to parse progress event:', parseError);
                    continue;
                  }
                }
              }
            }

            // If we reach here, the stream ended without completion
            const errorMessage = 'Stream ended unexpectedly';
            errorUpload(errorMessage);
            onError(errorMessage);
            reject(new Error(errorMessage));
          } catch (error) {
            console.error('Upload failed:', error);
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            errorUpload(errorMessage);
            onError(errorMessage);
            reject(error);
          }
        };

        reader.onerror = () => {
          const errorMessage = 'Failed to read file';
          errorUpload(errorMessage);
          onError(errorMessage);
          reject(new Error(errorMessage));
        };
      });

      await uploadPromise;
    } catch (error) {
      console.error('Upload failed:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      errorUpload(errorMessage);
      onError(errorMessage);
    }
  }, [
    file,
    abortController,
    state,
    endpoint,
    obsidianProgress,
    trackProgressUpdate,
    completeUpload,
    errorUpload,
    onSuccess,
    onError,
  ]);

  // Start upload when state changes to uploading
  useEffect(() => {
    if (state === 'uploading') {
      performUpload();
    }
  }, [state, performUpload]);

  // Handle cancel
  const handleCancel = useCallback(() => {
    if (abortController) {
      abortController.abort();
      cancelUpload();
    }
  }, [abortController, cancelUpload]);

  // Render based on state
  if (state === 'idle') {
    return (
      <div
        className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          disabled
            ? 'border-gray-300 bg-gray-50 text-gray-500'
            : 'border-gray-400 hover:border-gray-500 bg-white'
        }`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <input
          type="file"
          accept=".json"
          onChange={handleFileUpload}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={disabled}
        />
        <div className="space-y-2">
          <Upload className="mx-auto h-8 w-8 text-gray-400" />
          <div className="text-sm">
            <span className="font-medium text-blue-600 hover:text-blue-500">Click to upload</span>{' '}
            or drag and drop
          </div>
          <p className="text-xs text-gray-500">Tana JSON export file</p>
        </div>
      </div>
    );
  }

  if (state === 'fileSelected') {
    return (
      <div className="border rounded-lg p-4 bg-blue-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <FileText className="h-5 w-5 text-blue-600" />
            <div>
              <p className="text-sm font-medium text-gray-900">{file?.name}</p>
              <p className="text-xs text-gray-500">{(file?.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={handleCancel} disabled={disabled}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        <div className="mt-3">
          <Button onClick={() => startUpload()} disabled={disabled} className="w-full">
            Start Obsidian Export
          </Button>
        </div>
      </div>
    );
  }

  if (state === 'uploading' || state === 'processing') {
    return (
      <div className="border rounded-lg p-4 bg-blue-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <div>
              <p className="text-sm font-medium text-gray-900">Exporting to Obsidian...</p>
              {obsidianProgress.currentTopicName && (
                <p className="text-xs text-gray-500">
                  Processing: {obsidianProgress.currentTopicName}
                </p>
              )}
              {obsidianProgress.totalTopics > 0 && (
                <p className="text-xs text-gray-500">
                  {obsidianProgress.currentTopic} / {obsidianProgress.totalTopics} topics
                  {obsidianProgress.percentage > 0 && ` (${obsidianProgress.percentage}%)`}
                </p>
              )}
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={handleCancel} disabled={disabled}>
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  if (state === 'completed') {
    return (
      <div className="border rounded-lg p-4 bg-green-50">
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0">
            <div className="h-5 w-5 bg-green-600 rounded-full flex items-center justify-center">
              <div className="h-2 w-2 bg-white rounded-full"></div>
            </div>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">Obsidian Export Complete!</p>
            <p className="text-xs text-gray-500">
              Vault created at: {obsidianProgress.vaultPath || '~/vault'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (state === 'error') {
    return (
      <div className="border rounded-lg p-4 bg-red-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <div className="h-5 w-5 bg-red-600 rounded-full flex items-center justify-center">
                <X className="h-3 w-3 text-white" />
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">Export Failed</p>
              <p className="text-xs text-gray-500">{lastError}</p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return null;
}
