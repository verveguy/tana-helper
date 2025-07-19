import { useCallback } from 'react'
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

// Action hooks for cleaner component code - fixed to prevent infinite re-renders
export const useAppActions = () => {
  const setGraphData = useAppStoreBase(state => state.setGraphData)
  const setLoading = useAppStoreBase(state => state.setLoading)
  const setMermaidText = useAppStoreBase(state => state.setMermaidText)
  const setRagIndexData = useAppStoreBase(state => state.setRagIndexData)
  const setConfig = useAppStoreBase(state => state.setConfig)
  const setWebhooks = useAppStoreBase(state => state.setWebhooks)
  const setTwoDee = useAppStoreBase(state => state.setTwoDee)
  const setError = useAppStoreBase(state => state.setError)
  const clearError = useAppStoreBase(state => state.clearError)
  const resetState = useAppStoreBase(state => state.resetState)
  const loadConfig = useAppStoreBase(state => state.loadConfig)
  const saveConfig = useAppStoreBase(state => state.saveConfig)

  return {
    setGraphData,
    setLoading,
    setMermaidText,
    setRagIndexData,
    setConfig,
    setWebhooks,
    setTwoDee,
    setError,
    clearError,
    resetState,
    loadConfig,
    saveConfig,
  }
}

// Specific action hooks - also fixed for stability
export const useConfigActions = () => {
  const loadConfig = useAppStoreBase(state => state.loadConfig)
  const saveConfig = useAppStoreBase(state => state.saveConfig)
  const setConfig = useAppStoreBase(state => state.setConfig)

  return {
    loadConfig,
    saveConfig,
    setConfig,
  }
}

export const useGraphActions = () => {
  const setGraphData = useAppStoreBase(state => state.setGraphData)
  const setMermaidText = useAppStoreBase(state => state.setMermaidText)
  const setTwoDee = useAppStoreBase(state => state.setTwoDee)

  return {
    setGraphData,
    setMermaidText,
    setTwoDee,
  }
}

export const useErrorActions = () => {
  const setError = useAppStoreBase(state => state.setError)
  const clearError = useAppStoreBase(state => state.clearError)

  return {
    setError,
    clearError,
  }
}