import { useAppStore as useAppStoreBase } from '../store'
import { AppSelector } from '../store/types'

// Main store hook
export const useAppStore = () => useAppStoreBase()

// Optimized selector hook for performance
export const useAppStoreSelector = <T>(selector: AppSelector<T>) => 
  useAppStoreBase(selector)

// Convenience hooks for common selectors
export const useLoading = () => 
  useAppStoreBase(state => state.loading)

export const useError = () => 
  useAppStoreBase(state => state.error)

export const useGraphData = () => 
  useAppStoreBase(state => state.graphData)

export const useMermaidText = () => 
  useAppStoreBase(state => state.mermaidText)

export const useRagIndexData = () => 
  useAppStoreBase(state => state.ragIndexData)

export const useConfig = () => 
  useAppStoreBase(state => state.config)

export const useWebhooks = () => 
  useAppStoreBase(state => state.webhooks)

export const useTwoDee = () => 
  useAppStoreBase(state => state.twoDee)

// Action hooks for cleaner component code
export const useAppActions = () => 
  useAppStoreBase(state => ({
    setGraphData: state.setGraphData,
    setLoading: state.setLoading,
    setMermaidText: state.setMermaidText,
    setRagIndexData: state.setRagIndexData,
    setConfig: state.setConfig,
    setWebhooks: state.setWebhooks,
    setTwoDee: state.setTwoDee,
    setError: state.setError,
    clearError: state.clearError,
    resetState: state.resetState,
    loadConfig: state.loadConfig,
    saveConfig: state.saveConfig,
  }))

// Specific action hooks
export const useConfigActions = () => 
  useAppStoreBase(state => ({
    loadConfig: state.loadConfig,
    saveConfig: state.saveConfig,
    setConfig: state.setConfig,
  }))

export const useGraphActions = () => 
  useAppStoreBase(state => ({
    setGraphData: state.setGraphData,
    setMermaidText: state.setMermaidText,
    setTwoDee: state.setTwoDee,
  }))

export const useErrorActions = () => 
  useAppStoreBase(state => ({
    setError: state.setError,
    clearError: state.clearError,
  }))