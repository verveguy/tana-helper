// No React import needed for this file
import { useAppStore as useAppStoreBase } from '../store';
import { AppSelector } from '../store/types';

// Main store hook
export const useAppStore = () => useAppStoreBase();

// Optimized selector hook for performance
export const useAppStoreSelector = <T>(selector: AppSelector<T>) => useAppStoreBase(selector);

// Convenience hooks for common selectors
export const useLoading = () => useAppStoreBase(state => state.loading);

export const useVisualizerLoading = () => useAppStoreBase(state => state.visualizerLoading);

export const useClassLoading = () => useAppStoreBase(state => state.classLoading);

export const useRagLoading = () => useAppStoreBase(state => state.ragLoading);

export const useObsidianLoading = () => useAppStoreBase(state => state.obsidianLoading);

export const useConfigLoading = () => useAppStoreBase(state => state.configLoading);

export const useError = () => useAppStoreBase(state => state.error);

export const useVisualizerError = () => useAppStoreBase(state => state.visualizerError);

export const useClassError = () => useAppStoreBase(state => state.classError);

export const useRagError = () => useAppStoreBase(state => state.ragError);

export const useObsidianError = () => useAppStoreBase(state => state.obsidianError);

export const useConfigError = () => useAppStoreBase(state => state.configError);

export const useGraphData = () => useAppStoreBase(state => state.graphData);

export const useMermaidText = () => useAppStoreBase(state => state.mermaidText);

export const useRagIndexData = () => useAppStoreBase(state => state.ragIndexData);

export const useRagProgress = () => useAppStoreBase(state => state.ragProgress);

export const useObsidianExportData = () => useAppStoreBase(state => state.obsidianExportData);

export const useObsidianProgress = () => useAppStoreBase(state => state.obsidianProgress);

export const useConfig = () => useAppStoreBase(state => state.config);

export const useWebhooks = () => useAppStoreBase(state => state.webhooks);

export const useTwoDee = () => useAppStoreBase(state => state.twoDee);

export const useSidebarCollapsed = () => useAppStoreBase(state => state.sidebarCollapsed);

// Action hooks for cleaner component code - fixed to prevent infinite re-renders
export const useAppActions = () => {
  const setGraphData = useAppStoreBase(state => state.setGraphData);
  const setLoading = useAppStoreBase(state => state.setLoading);
  const setVisualizerLoading = useAppStoreBase(state => state.setVisualizerLoading);
  const setClassLoading = useAppStoreBase(state => state.setClassLoading);
  const setRagLoading = useAppStoreBase(state => state.setRagLoading);
  const setObsidianLoading = useAppStoreBase(state => state.setObsidianLoading);
  const setConfigLoading = useAppStoreBase(state => state.setConfigLoading);
  const setMermaidText = useAppStoreBase(state => state.setMermaidText);
  const setRagIndexData = useAppStoreBase(state => state.setRagIndexData);
  const setRagProgress = useAppStoreBase(state => state.setRagProgress);
  const resetRagProgress = useAppStoreBase(state => state.resetRagProgress);
  const updateRagProgress = useAppStoreBase(state => state.updateRagProgress);
  const setObsidianExportData = useAppStoreBase(state => state.setObsidianExportData);
  const setObsidianProgress = useAppStoreBase(state => state.setObsidianProgress);
  const resetObsidianProgress = useAppStoreBase(state => state.resetObsidianProgress);
  const updateObsidianProgress = useAppStoreBase(state => state.updateObsidianProgress);
  const setConfig = useAppStoreBase(state => state.setConfig);
  const setWebhooks = useAppStoreBase(state => state.setWebhooks);
  const setTwoDee = useAppStoreBase(state => state.setTwoDee);
  const setSidebarCollapsed = useAppStoreBase(state => state.setSidebarCollapsed);
  const setError = useAppStoreBase(state => state.setError);
  const setVisualizerError = useAppStoreBase(state => state.setVisualizerError);
  const setClassError = useAppStoreBase(state => state.setClassError);
  const setRagError = useAppStoreBase(state => state.setRagError);
  const setObsidianError = useAppStoreBase(state => state.setObsidianError);
  const setConfigError = useAppStoreBase(state => state.setConfigError);
  const clearError = useAppStoreBase(state => state.clearError);
  const resetState = useAppStoreBase(state => state.resetState);
  const resetVisualizerState = useAppStoreBase(state => state.resetVisualizerState);
  const resetClassDiagramState = useAppStoreBase(state => state.resetClassDiagramState);
  const resetRAGIndexState = useAppStoreBase(state => state.resetRAGIndexState);
  const resetObsidianState = useAppStoreBase(state => state.resetObsidianState);
  const loadConfig = useAppStoreBase(state => state.loadConfig);
  const saveConfig = useAppStoreBase(state => state.saveConfig);

  return {
    setGraphData,
    setLoading,
    setVisualizerLoading,
    setClassLoading,
    setRagLoading,
    setObsidianLoading,
    setConfigLoading,
    setMermaidText,
    setRagIndexData,
    setRagProgress,
    resetRagProgress,
    updateRagProgress,
    setObsidianExportData,
    setObsidianProgress,
    resetObsidianProgress,
    updateObsidianProgress,
    setConfig,
    setWebhooks,
    setTwoDee,
    setSidebarCollapsed,
    setError,
    setVisualizerError,
    setClassError,
    setRagError,
    setObsidianError,
    setConfigError,
    clearError,
    resetState,
    resetVisualizerState,
    resetClassDiagramState,
    resetRAGIndexState,
    resetObsidianState,
    loadConfig,
    saveConfig,
  };
};

// Specific action hooks - also fixed for stability
export const useConfigActions = () => {
  const loadConfig = useAppStoreBase(state => state.loadConfig);
  const saveConfig = useAppStoreBase(state => state.saveConfig);
  const setConfig = useAppStoreBase(state => state.setConfig);

  return {
    loadConfig,
    saveConfig,
    setConfig,
  };
};

export const useGraphActions = () => {
  const setGraphData = useAppStoreBase(state => state.setGraphData);
  const setMermaidText = useAppStoreBase(state => state.setMermaidText);
  const setTwoDee = useAppStoreBase(state => state.setTwoDee);

  return {
    setGraphData,
    setMermaidText,
    setTwoDee,
  };
};

export const useErrorActions = () => {
  const setError = useAppStoreBase(state => state.setError);
  const clearError = useAppStoreBase(state => state.clearError);

  return {
    setError,
    clearError,
  };
};

// Upload State Machine hooks
export const useUploadMachine = () => useAppStoreBase(state => state.uploadMachine);

export const useUploadState = () => useAppStoreBase(state => state.uploadMachine.state);

export const useUploadContext = () => useAppStoreBase(state => state.uploadMachine.context);

export const useUploadActions = () => {
  const selectFile = useAppStoreBase(state => state.selectFile);
  const startUpload = useAppStoreBase(state => state.startUpload);
  const updateUploadProgress = useAppStoreBase(state => state.updateUploadProgress);
  const cancelUpload = useAppStoreBase(state => state.cancelUpload);
  const completeUpload = useAppStoreBase(state => state.completeUpload);
  const errorUpload = useAppStoreBase(state => state.errorUpload);
  const retryUpload = useAppStoreBase(state => state.retryUpload);
  const resetUpload = useAppStoreBase(state => state.resetUpload);
  const sendUploadEvent = useAppStoreBase(state => state.sendUploadEvent);

  return {
    selectFile,
    startUpload,
    updateUploadProgress,
    cancelUpload,
    completeUpload,
    errorUpload,
    retryUpload,
    resetUpload,
    sendUploadEvent,
  };
};
