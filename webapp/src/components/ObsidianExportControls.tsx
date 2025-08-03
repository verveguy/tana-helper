// React import not needed for JSX in React 17+
import TanaStreamingUpload from './ui/TanaStreamingUpload';
// Replace context with Zustand store
import { useUploadMachine, useUploadActions } from '../hooks/useAppStore';

// 🎯 SIMPLIFIED: Helper function to determine if upload should be disabled
function shouldDisableUpload(uploadState: string, obsidianProgress: any): boolean {
  // Disable during active upload/processing states
  if (uploadState === 'uploading' || uploadState === 'processing' || uploadState === 'cancelling') {
    return true;
  }

  // Disable during active Obsidian progress (except when idle or complete)
  if (
    obsidianProgress.isActive &&
    obsidianProgress.phase !== 'idle' &&
    obsidianProgress.phase !== 'complete'
  ) {
    return true;
  }

  return false;
}

export default function ObsidianExportControls() {
  const uploadMachine = useUploadMachine();
  // Note: Upload actions are handled internally by TanaStreamingUpload
  // const uploadActions = useUploadActions(); // Not needed here

  const { state, context } = uploadMachine;
  const { obsidianProgress } = context;

  const handleUploadSuccess = (data: any) => {
    console.log('Obsidian export streaming completed:', data);
    // Note: completeUpload is already called by TanaStreamingUpload component
    // This callback is just for additional success handling if needed
  };

  const handleUploadError = (errorMessage: string) => {
    console.error('Obsidian export upload failed:', errorMessage);
    // Note: errorUpload is already called by TanaStreamingUpload component
    // This callback is just for additional error handling if needed
  };

  // 🎯 SIMPLIFIED: Clear disable logic
  const isUploadDisabled = shouldDisableUpload(state, obsidianProgress);

  // Obsidian-specific progress handler
  const obsidianProgressHandler = (eventData: any, currentProgress: any) => {
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
        return {}; // Return empty update for unknown events
    }
  };

  // Obsidian-specific event validator
  const obsidianEventValidator = (data: any) => {
    return (
      data &&
      typeof data === 'object' &&
      typeof data.type === 'string' &&
      ['starting', 'processing', 'complete'].includes(data.type)
    );
  };

  return (
    <TanaStreamingUpload
      endpoint="/migrate/obsidian"
      onSuccess={handleUploadSuccess}
      onError={handleUploadError}
      disabled={isUploadDisabled}
      progressHandler={obsidianProgressHandler}
      eventValidator={obsidianEventValidator}
      uploadButtonText="Start Obsidian Export"
      dropZoneText="Tana JSON export file"
    />
  );
}
