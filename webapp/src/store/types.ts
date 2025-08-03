// Core data types
export interface GraphData {
  nodes: Array<{
    id: string;
    name: string;
    [key: string]: any;
  }>;
  links: Array<{
    source: string;
    target: string;
    [key: string]: any;
  }>;
}

export interface RAGIndexData {
  documents: Array<{
    id: string;
    content: string;
    metadata: Record<string, any>;
  }>;
  [key: string]: any;
}

export interface ObsidianExportData {
  vaultPath?: string;
  topicCount: number;
  exportedAt: string;
  [key: string]: any;
}

// Progress state for RAG indexing operations
export interface RAGProgressState {
  isActive: boolean;
  phase:
    | 'idle'
    | 'starting'
    | 'processing'
    | 'complete'
    | 'error'
    | 'batch_processing'
    | 'deletion'
    | 'deletion_complete'
    | 'embedding'
    | 'storing';
  currentTopic: number;
  totalTopics: number;
  currentNode: number;
  totalNodes: number;
  percentage: number;
  currentTopicName?: string;
  currentTopicId?: string;
  elapsedSeconds?: number;
  etaSeconds?: number;
  processingRate?: number;
  topicNode?: number;
  topicNodes?: number;
  error?: string;
  errorType?: string;
  errorHelp?: string;
  // Legacy batch processing progress (deprecated - use phase-specific)
  currentBatch?: number;
  totalBatches?: number;
  // Storage failure tracking
  failedNodes?: number;
  // Change detection optimization
  skippedTopics?: number;
  changedTopics?: number;
  // Incremental deletion tracking
  deletedNodes?: number;
  totalNodesToDelete?: number;
  deletionEta?: number;

  // Track which phases were explicitly skipped by the backend
  skippedPhases?: {
    [phaseId: string]: {
      skipped: boolean;
      reason: string;
    };
  };

  // Note: Phase timing is now handled client-side within individual PhaseItem components

  // Phase-specific progress tracking
  collection?: {
    current: number;
    total: number;
    completed: boolean;
  };
  embedding?: {
    current: number;
    total: number;
    batch: number;
    totalBatches: number;
    completed: boolean;
  };
  storage?: {
    current: number;
    total: number;
    batch: number;
    totalBatches: number;
    completed: boolean;
  };
}

// Progress state for Obsidian export operations
export interface ObsidianProgressState {
  isActive: boolean;
  phase: 'idle' | 'starting' | 'processing' | 'complete' | 'error' | 'converting' | 'writing_vault';
  currentTopic: number;
  totalTopics: number;
  percentage: number;
  currentTopicName?: string;
  currentTopicId?: string;
  elapsedSeconds?: number;
  etaSeconds?: number;
  processingRate?: number;
  error?: string;
  errorType?: string;
  errorHelp?: string;
  vaultPath?: string;
}

export interface Config {
  openai_api_key?: string;
  [key: string]: any;
}

export interface Webhook {
  id: string;
  url: string;
  events: string[];
  [key: string]: any;
}

// Store state interface
export interface AppState {
  // Core application state
  graphData?: GraphData;
  loading: boolean; // Legacy - kept for backward compatibility
  visualizerLoading: boolean;
  classLoading: boolean;
  ragLoading: boolean;
  obsidianLoading: boolean;
  configLoading: boolean;
  mermaidText?: string;
  ragIndexData?: RAGIndexData;
  ragProgress: RAGProgressState;
  obsidianExportData?: ObsidianExportData;
  obsidianProgress: ObsidianProgressState;
  config?: Config;
  webhooks?: Webhook[];
  twoDee: boolean;
  sidebarCollapsed: boolean;
  error: string | null; // Legacy - kept for backward compatibility
  visualizerError: string | null;
  classError: string | null;
  ragError: string | null;
  obsidianError: string | null;
  configError: string | null;

  // Upload State Machine
  uploadMachine: UploadMachine;
}

// Store actions interface
export interface AppActions {
  // Basic setters
  setGraphData: (graphData?: GraphData) => void;
  setLoading: (loading: boolean) => void; // Legacy - kept for backward compatibility
  setVisualizerLoading: (loading: boolean) => void;
  setClassLoading: (loading: boolean) => void;
  setRagLoading: (loading: boolean) => void;
  setObsidianLoading: (loading: boolean) => void;
  setConfigLoading: (loading: boolean) => void;
  setMermaidText: (mermaidText?: string) => void;
  setRagIndexData: (ragIndexData?: RAGIndexData) => void;
  setRagProgress: (progress: Partial<RAGProgressState>) => void;
  resetRagProgress: () => void;
  updateRagProgress: (updates: Partial<RAGProgressState>) => void;
  setObsidianExportData: (obsidianExportData?: ObsidianExportData) => void;
  setObsidianProgress: (progress: Partial<ObsidianProgressState>) => void;
  resetObsidianProgress: () => void;
  updateObsidianProgress: (updates: Partial<ObsidianProgressState>) => void;
  setConfig: (config?: Config) => void;
  setWebhooks: (webhooks?: Webhook[]) => void;
  setTwoDee: (twoDee: boolean) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setError: (error: string | null) => void; // Legacy - kept for backward compatibility
  setVisualizerError: (error: string | null) => void;
  setClassError: (error: string | null) => void;
  setRagError: (error: string | null) => void;
  setObsidianError: (error: string | null) => void;
  setConfigError: (error: string | null) => void;

  // Utility actions
  clearError: () => void;
  resetState: () => void;
  resetVisualizerState: () => void;
  resetClassDiagramState: () => void;
  resetRAGIndexState: () => void;
  resetObsidianState: () => void;

  // Async actions
  loadConfig: () => Promise<Config>;
  saveConfig: (config: Config) => Promise<Config>;

  // Upload State Machine actions
  sendUploadEvent: (event: UploadEvent) => void;
  selectFile: (file: File) => void;
  startUpload: () => void;
  updateUploadProgress: (progress: Partial<RAGProgressState>) => void;
  cancelUpload: () => void;
  completeUpload: (data?: any) => void;
  errorUpload: (error: string) => void;
  retryUpload: () => void;
  resetUpload: () => void;
}

// Upload State Machine Types
export type UploadState =
  | 'idle'
  | 'fileSelected'
  | 'uploading'
  | 'processing'
  | 'cancelling'
  | 'completed'
  | 'error';

export type UploadEvent =
  | { type: 'SELECT_FILE'; file: File }
  | { type: 'START_UPLOAD' }
  | { type: 'UPLOAD_PROGRESS'; progress: Partial<RAGProgressState> }
  | { type: 'CANCEL' }
  | { type: 'CANCELLED' }
  | { type: 'COMPLETE'; data?: any }
  | { type: 'ERROR'; error: string }
  | { type: 'RETRY' }
  | { type: 'RESET' };

export interface UploadContext {
  file: File | null;
  abortController: AbortController | null;
  ragProgress: RAGProgressState;
  obsidianProgress: ObsidianProgressState;
  lastError: string | null;
  completionData: any | null;
}

export interface UploadMachine {
  state: UploadState;
  context: UploadContext;
  canTransition: (event: UploadEvent) => boolean;
  send: (event: UploadEvent) => void;
}

// Selector types for optimized component subscriptions
export type AppSelector<T> = (state: AppState & AppActions) => T;

// Hook types
export type UseAppStore = () => AppState & AppActions;
export type UseAppStoreSelector = <T>(selector: AppSelector<T>) => T;
