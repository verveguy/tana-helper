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

// Progress state for RAG indexing operations
export interface RAGProgressState {
  isActive: boolean;
  phase: 'idle' | 'starting' | 'processing' | 'complete' | 'error';

  // Overall progress
  currentTopic: number;
  totalTopics: number;
  currentNode: number;
  totalNodes: number;
  percentage: number;

  // Current processing info
  currentTopicName?: string;
  currentTopicId?: string;

  // Timing information
  elapsedSeconds?: number;
  etaSeconds?: number;
  processingRate?: number; // nodes per second

  // Error information
  error?: string;

  // Topic-level progress for large topics
  topicNode?: number;
  topicNodes?: number;
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
  configLoading: boolean;
  mermaidText?: string;
  ragIndexData?: RAGIndexData;
  ragProgress: RAGProgressState;
  config?: Config;
  webhooks?: Webhook[];
  twoDee: boolean;
  sidebarCollapsed: boolean;
  error: string | null; // Legacy - kept for backward compatibility
  visualizerError: string | null;
  classError: string | null;
  ragError: string | null;
  configError: string | null;
}

// Store actions interface
export interface AppActions {
  // Basic setters
  setGraphData: (graphData?: GraphData) => void;
  setLoading: (loading: boolean) => void; // Legacy - kept for backward compatibility
  setVisualizerLoading: (loading: boolean) => void;
  setClassLoading: (loading: boolean) => void;
  setRagLoading: (loading: boolean) => void;
  setConfigLoading: (loading: boolean) => void;
  setMermaidText: (mermaidText?: string) => void;
  setRagIndexData: (ragIndexData?: RAGIndexData) => void;
  setRagProgress: (progress: Partial<RAGProgressState>) => void;
  resetRagProgress: () => void;
  updateRagProgress: (updates: Partial<RAGProgressState>) => void;
  setConfig: (config?: Config) => void;
  setWebhooks: (webhooks?: Webhook[]) => void;
  setTwoDee: (twoDee: boolean) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setError: (error: string | null) => void; // Legacy - kept for backward compatibility
  setVisualizerError: (error: string | null) => void;
  setClassError: (error: string | null) => void;
  setRagError: (error: string | null) => void;
  setConfigError: (error: string | null) => void;

  // Utility actions
  clearError: () => void;
  resetState: () => void;
  resetVisualizerState: () => void;
  resetClassDiagramState: () => void;
  resetRAGIndexState: () => void;

  // Async actions
  loadConfig: () => Promise<Config>;
  saveConfig: (config: Config) => Promise<Config>;
}

// Selector types for optimized component subscriptions
export type AppSelector<T> = (state: AppState & AppActions) => T;

// Hook types
export type UseAppStore = () => AppState & AppActions;
export type UseAppStoreSelector = <T>(selector: AppSelector<T>) => T;
