// Core data types
export interface GraphData {
  nodes: Array<{
    id: string
    name: string
    [key: string]: any
  }>
  links: Array<{
    source: string
    target: string
    [key: string]: any
  }>
}

export interface RAGIndexData {
  documents: Array<{
    id: string
    content: string
    metadata: Record<string, any>
  }>
  [key: string]: any
}

export interface Config {
  openai_api_key?: string
  [key: string]: any
}

export interface Webhook {
  id: string
  url: string
  events: string[]
  [key: string]: any
}

// Store state interface
export interface AppState {
  // Core application state
  graphData?: GraphData
  loading: boolean
  mermaidText?: string
  ragIndexData?: RAGIndexData
  config?: Config
  webhooks?: Webhook[]
  twoDee: boolean
  error: string | null
}

// Store actions interface
export interface AppActions {
  // Basic setters
  setGraphData: (graphData?: GraphData) => void
  setLoading: (loading: boolean) => void
  setMermaidText: (mermaidText?: string) => void
  setRagIndexData: (ragIndexData?: RAGIndexData) => void
  setConfig: (config?: Config) => void
  setWebhooks: (webhooks?: Webhook[]) => void
  setTwoDee: (twoDee: boolean) => void
  setError: (error: string | null) => void
  
  // Utility actions
  clearError: () => void
  resetState: () => void
  
  // Async actions
  loadConfig: () => Promise<Config>
  saveConfig: (config: Config) => Promise<Config>
}

// Selector types for optimized component subscriptions
export type AppSelector<T> = (state: AppState & AppActions) => T

// Hook types
export type UseAppStore = () => AppState & AppActions
export type UseAppStoreSelector = <T>(selector: AppSelector<T>) => T