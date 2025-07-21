import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { AppState, AppActions, RAGProgressState } from './types';

// Default RAG progress state
const defaultRAGProgress: RAGProgressState = {
  isActive: false,
  phase: 'idle',
  currentTopic: 0,
  totalTopics: 0,
  currentNode: 0,
  totalNodes: 0,
  percentage: 0,
};

// Core app store with devtools and persistence for configuration
export const useAppStore = create<AppState & AppActions>()(
  devtools(
    persist(
      (set, get) => ({
        // State
        graphData: undefined,
        loading: false, // Legacy - kept for backward compatibility
        visualizerLoading: false,
        classLoading: false,
        ragLoading: false,
        configLoading: false,
        mermaidText: undefined,
        ragIndexData: undefined,
        ragProgress: defaultRAGProgress,
        config: undefined,
        webhooks: undefined,
        twoDee: false,
        sidebarCollapsed: false,
        error: null, // Legacy - kept for backward compatibility
        visualizerError: null,
        classError: null,
        ragError: null,
        configError: null,

        // Actions
        setGraphData: graphData => set({ graphData }, false, 'setGraphData'),

        setLoading: loading => set({ loading }, false, 'setLoading'),

        setVisualizerLoading: visualizerLoading =>
          set({ visualizerLoading }, false, 'setVisualizerLoading'),

        setClassLoading: classLoading => set({ classLoading }, false, 'setClassLoading'),

        setRagLoading: ragLoading => set({ ragLoading }, false, 'setRagLoading'),

        setConfigLoading: configLoading => set({ configLoading }, false, 'setConfigLoading'),

        setMermaidText: mermaidText => set({ mermaidText }, false, 'setMermaidText'),

        setRagIndexData: ragIndexData => set({ ragIndexData }, false, 'setRagIndexData'),

        setRagProgress: progress =>
          set({ ragProgress: { ...get().ragProgress, ...progress } }, false, 'setRagProgress'),

        resetRagProgress: () => set({ ragProgress: defaultRAGProgress }, false, 'resetRagProgress'),

        updateRagProgress: updates =>
          set(
            state => ({ ragProgress: { ...state.ragProgress, ...updates } }),
            false,
            'updateRagProgress'
          ),

        setConfig: config => set({ config }, false, 'setConfig'),

        setWebhooks: webhooks => set({ webhooks }, false, 'setWebhooks'),

        setTwoDee: twoDee => set({ twoDee }, false, 'setTwoDee'),

        setSidebarCollapsed: sidebarCollapsed =>
          set({ sidebarCollapsed }, false, 'setSidebarCollapsed'),

        setError: error => set({ error }, false, 'setError'),

        setVisualizerError: visualizerError =>
          set({ visualizerError }, false, 'setVisualizerError'),

        setClassError: classError => set({ classError }, false, 'setClassError'),

        setRagError: ragError => set({ ragError }, false, 'setRagError'),

        setConfigError: configError => set({ configError }, false, 'setConfigError'),

        // Computed/derived actions
        clearError: () => set({ error: null }, false, 'clearError'),

        resetState: () =>
          set(
            {
              graphData: undefined,
              loading: false,
              mermaidText: undefined,
              ragIndexData: undefined,
              error: null,
              twoDee: false,
            },
            false,
            'resetState'
          ),

        // Component-specific reset actions
        resetVisualizerState: () =>
          set(
            {
              graphData: undefined,
              visualizerError: null,
              visualizerLoading: false,
            },
            false,
            'resetVisualizerState'
          ),

        resetClassDiagramState: () =>
          set(
            {
              mermaidText: undefined,
              classError: null,
              classLoading: false,
            },
            false,
            'resetClassDiagramState'
          ),

        resetRAGIndexState: () =>
          set(
            {
              ragIndexData: undefined,
              ragError: null,
              ragLoading: false,
              ragProgress: defaultRAGProgress,
            },
            false,
            'resetRAGIndexState'
          ),

        // Async actions
        loadConfig: async () => {
          set({ configLoading: true, configError: null }, false, 'loadConfig:start');
          try {
            const response = await fetch('/configure');
            if (!response.ok) {
              throw new Error(`Failed to load config: ${response.statusText}`);
            }
            const config = await response.json();
            set({ config, configLoading: false }, false, 'loadConfig:success');
            return config;
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            set(
              {
                configError: errorMessage,
                configLoading: false,
              },
              false,
              'loadConfig:error'
            );
            throw error;
          }
        },

        saveConfig: async newConfig => {
          set({ configLoading: true, configError: null }, false, 'saveConfig:start');
          try {
            const response = await fetch('/configure', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(newConfig),
            });
            if (!response.ok) {
              throw new Error(`Failed to save config: ${response.statusText}`);
            }
            const savedConfig = await response.json();
            set(
              {
                config: savedConfig,
                configLoading: false,
              },
              false,
              'saveConfig:success'
            );
            return savedConfig;
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            set(
              {
                configError: errorMessage,
                configLoading: false,
              },
              false,
              'saveConfig:error'
            );
            throw error;
          }
        },
      }),
      {
        name: 'tana-helper-storage',
        // Only persist configuration, not temporary data
        partialize: state => ({
          config: state.config,
          twoDee: state.twoDee,
          sidebarCollapsed: state.sidebarCollapsed,
        }),
      }
    ),
    {
      name: 'tana-helper-store',
    }
  )
);
