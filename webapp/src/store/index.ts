import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { AppState, AppActions } from './types'

// Core app store with devtools and persistence for configuration
export const useAppStore = create<AppState & AppActions>()(
  devtools(
    persist(
      (set, get) => ({
        // State
        graphData: undefined,
        loading: false,
        mermaidText: undefined,
        ragIndexData: undefined,
        config: undefined,
        webhooks: undefined,
        twoDee: false,
        error: null,
        
        // Actions
        setGraphData: (graphData) => set({ graphData }, false, 'setGraphData'),
        
        setLoading: (loading) => set({ loading }, false, 'setLoading'),
        
        setMermaidText: (mermaidText) => set({ mermaidText }, false, 'setMermaidText'),
        
        setRagIndexData: (ragIndexData) => set({ ragIndexData }, false, 'setRagIndexData'),
        
        setConfig: (config) => set({ config }, false, 'setConfig'),
        
        setWebhooks: (webhooks) => set({ webhooks }, false, 'setWebhooks'),
        
        setTwoDee: (twoDee) => set({ twoDee }, false, 'setTwoDee'),
        
        setError: (error) => set({ error }, false, 'setError'),
        
        // Computed/derived actions
        clearError: () => set({ error: null }, false, 'clearError'),
        
        resetState: () => set({
          graphData: undefined,
          loading: false,
          mermaidText: undefined,
          ragIndexData: undefined,
          error: null,
          twoDee: false
        }, false, 'resetState'),
        
        // Async actions
        loadConfig: async () => {
          set({ loading: true, error: null }, false, 'loadConfig:start')
          try {
            const response = await fetch('/configure')
            if (!response.ok) {
              throw new Error(`Failed to load config: ${response.statusText}`)
            }
            const config = await response.json()
            set({ config, loading: false }, false, 'loadConfig:success')
            return config
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error'
            set({ 
              error: errorMessage, 
              loading: false 
            }, false, 'loadConfig:error')
            throw error
          }
        },
        
        saveConfig: async (newConfig) => {
          set({ loading: true, error: null }, false, 'saveConfig:start')
          try {
            const response = await fetch('/configure', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(newConfig)
            })
            if (!response.ok) {
              throw new Error(`Failed to save config: ${response.statusText}`)
            }
            const savedConfig = await response.json()
            set({ 
              config: savedConfig, 
              loading: false 
            }, false, 'saveConfig:success')
            return savedConfig
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error'
            set({ 
              error: errorMessage, 
              loading: false 
            }, false, 'saveConfig:error')
            throw error
          }
        }
      }),
      {
        name: 'tana-helper-storage',
        // Only persist configuration, not temporary data
        partialize: (state) => ({ 
          config: state.config,
          twoDee: state.twoDee 
        }),
      }
    ),
    {
      name: 'tana-helper-store',
    }
  )
)