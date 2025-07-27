import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import {
  AppState,
  AppActions,
  RAGProgressState,
  UploadState,
  UploadEvent,
  UploadContext,
  UploadMachine,
} from './types';

// Default RAG progress state
const defaultRAGProgress: RAGProgressState = {
  isActive: false,
  phase: 'idle',
  currentTopic: 0,
  totalTopics: 0,
  currentNode: 0,
  totalNodes: 0,
  percentage: 0,
  skippedPhases: {},
};

// Default upload context
const defaultUploadContext: UploadContext = {
  file: null,
  abortController: null,
  ragProgress: defaultRAGProgress,
  lastError: null,
  completionData: null,
};

// Upload State Machine Implementation
const createUploadMachine = (
  setState: (partial: Partial<AppState>) => void,
  getState: () => AppState & AppActions
): UploadMachine => {
  let currentState: UploadState = 'idle';
  let context: UploadContext = { ...defaultUploadContext };

  // State transition logic
  const transitions: Record<UploadState, Record<string, UploadState>> = {
    idle: {
      SELECT_FILE: 'fileSelected',
    },
    fileSelected: {
      START_UPLOAD: 'uploading',
      SELECT_FILE: 'fileSelected', // Allow file replacement
      RESET: 'idle',
    },
    uploading: {
      UPLOAD_PROGRESS: 'processing',
      CANCEL: 'cancelling',
      ERROR: 'error',
      COMPLETE: 'completed',
    },
    processing: {
      UPLOAD_PROGRESS: 'processing', // Stay in processing
      CANCEL: 'cancelling',
      ERROR: 'error',
      COMPLETE: 'completed',
    },
    cancelling: {
      CANCELLED: 'idle',
      ERROR: 'error', // Cancellation failed
    },
    completed: {
      SELECT_FILE: 'fileSelected',
      RESET: 'idle',
      // Don't allow COMPLETE again - already completed
    },
    error: {
      SELECT_FILE: 'fileSelected',
      RETRY: 'uploading',
      RESET: 'idle',
    },
  };

  const canTransition = (event: UploadEvent): boolean => {
    const allowedTransitions = transitions[currentState];
    return event.type in allowedTransitions;
  };

  const send = (event: UploadEvent): void => {
    console.log(`🎯 Upload State Machine: ${currentState} + ${event.type}`);

    if (!canTransition(event)) {
      console.warn(`❌ Invalid transition: ${currentState} + ${event.type}`);
      return;
    }

    const nextState = transitions[currentState][event.type];
    const prevState = currentState;
    currentState = nextState;

    // Handle side effects for state transitions
    switch (event.type) {
      case 'SELECT_FILE':
        context = {
          ...context,
          file: event.file,
          lastError: null,
          completionData: null,
          ragProgress: { ...defaultRAGProgress },
        };
        break;

      case 'START_UPLOAD':
        // Create abort controller for this upload
        context = {
          ...context,
          abortController: new AbortController(),
          ragProgress: { ...defaultRAGProgress, isActive: true, phase: 'starting' },
          lastError: null,
        };
        break;

      case 'UPLOAD_PROGRESS':
        context = {
          ...context,
          ragProgress: { ...context.ragProgress, ...event.progress },
        };
        break;

      case 'CANCEL':
        // Abort the request and clean up
        if (context.abortController) {
          context.abortController.abort();
        }
        break;

      case 'CANCELLED':
        context = {
          ...context,
          abortController: null,
          ragProgress: { ...defaultRAGProgress },
        };
        break;

      case 'COMPLETE':
        context = {
          ...context,
          abortController: null,
          completionData: event.data,
          ragProgress: {
            ...context.ragProgress,
            ...(event.data?.finalProgress || {}),
            phase: 'complete',
            isActive: false,
          },
        };
        break;

      case 'ERROR':
        context = {
          ...context,
          abortController: null,
          lastError: event.error,
          ragProgress: {
            ...context.ragProgress,
            phase: 'error',
            isActive: false,
            error: event.error,
          },
        };
        break;

      case 'RETRY':
        context = {
          ...context,
          lastError: null,
          ragProgress: { ...defaultRAGProgress },
        };
        break;

      case 'RESET':
        context = { ...defaultUploadContext };
        break;
    }

    console.log(`✅ Upload State: ${prevState} → ${currentState}`);

    // Update the store with new state and context
    setState({
      uploadMachine: {
        state: currentState,
        context: { ...context },
        canTransition,
        send,
      },
      // Sync legacy ragProgress for backward compatibility
      ragProgress: context.ragProgress,
      // 🎯 CONSOLIDATED: Derive ragLoading and ragError from state machine
      ragLoading: currentState === 'uploading' || currentState === 'processing',
      ragError: context.lastError,
    });
  };

  return {
    state: currentState,
    context: { ...context },
    canTransition,
    send,
  };
};

// Core app store with devtools and persistence for configuration
export const useAppStore = create<AppState & AppActions>()(
  devtools(
    persist(
      (set, get) => {
        // Initialize upload machine
        const uploadMachine = createUploadMachine(
          partial => set(partial, false, 'uploadMachine:update'),
          get
        );

        return {
          // State
          graphData: undefined,
          loading: false, // Legacy - kept for backward compatibility
          visualizerLoading: false,
          classLoading: false,
          ragLoading: false, // 🎯 DERIVED: Now derived from state machine
          configLoading: false,
          mermaidText: undefined,
          ragIndexData: undefined,
          ragProgress: defaultRAGProgress, // 🎯 DERIVED: Now derived from state machine
          config: undefined,
          webhooks: undefined,
          twoDee: false,
          sidebarCollapsed: false,
          error: null, // Legacy - kept for backward compatibility
          visualizerError: null,
          classError: null,
          ragError: null, // 🎯 DERIVED: Now derived from state machine
          configError: null,

          // Upload State Machine
          uploadMachine,

          // Actions
          setGraphData: graphData => set({ graphData }, false, 'setGraphData'),

          setLoading: loading => set({ loading }, false, 'setLoading'),

          setVisualizerLoading: visualizerLoading =>
            set({ visualizerLoading }, false, 'setVisualizerLoading'),

          setClassLoading: classLoading => set({ classLoading }, false, 'setClassLoading'),

          // 🎯 DEPRECATED: Use state machine instead
          setRagLoading: ragLoading => {
            console.warn('setRagLoading is deprecated, use upload state machine instead');
            set({ ragLoading }, false, 'setRagLoading');
          },

          setConfigLoading: configLoading => set({ configLoading }, false, 'setConfigLoading'),

          setMermaidText: mermaidText => set({ mermaidText }, false, 'setMermaidText'),

          setRagIndexData: ragIndexData => set({ ragIndexData }, false, 'setRagIndexData'),

          // 🎯 DEPRECATED: Use state machine instead
          setRagProgress: progress => {
            console.warn('setRagProgress is deprecated, use updateUploadProgress instead');
            set({ ragProgress: { ...get().ragProgress, ...progress } }, false, 'setRagProgress');
          },

          // 🎯 DEPRECATED: Use state machine instead
          resetRagProgress: () => {
            console.warn('resetRagProgress is deprecated, use resetUpload instead');
            set({ ragProgress: defaultRAGProgress }, false, 'resetRagProgress');
          },

          // 🎯 DEPRECATED: Use state machine instead
          updateRagProgress: updates => {
            console.warn('updateRagProgress is deprecated, use updateUploadProgress instead');
            set(
              state => ({ ragProgress: { ...state.ragProgress, ...updates } }),
              false,
              'updateRagProgress'
            );
          },

          setConfig: config => set({ config }, false, 'setConfig'),

          setWebhooks: webhooks => set({ webhooks }, false, 'setWebhooks'),

          setTwoDee: twoDee => set({ twoDee }, false, 'setTwoDee'),

          setSidebarCollapsed: sidebarCollapsed =>
            set({ sidebarCollapsed }, false, 'setSidebarCollapsed'),

          setError: error => set({ error }, false, 'setError'),

          setVisualizerError: visualizerError =>
            set({ visualizerError }, false, 'setVisualizerError'),

          setClassError: classError => set({ classError }, false, 'setClassError'),

          // 🎯 DEPRECATED: Use state machine instead
          setRagError: ragError => {
            console.warn('setRagError is deprecated, use errorUpload instead');
            set({ ragError }, false, 'setRagError');
          },

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

          // 🎯 UPDATED: Use state machine for RAG state reset
          resetRAGIndexState: () => {
            const machine = get().uploadMachine;
            machine.send({ type: 'RESET' });
            set(
              {
                ragIndexData: undefined,
                // ragError and ragLoading are now derived from state machine
              },
              false,
              'resetRAGIndexState'
            );
          },

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

          // 🎯 CONSOLIDATED: Upload State Machine actions
          sendUploadEvent: event => {
            const machine = get().uploadMachine;
            machine.send(event);
          },

          selectFile: file => {
            const machine = get().uploadMachine;
            machine.send({ type: 'SELECT_FILE', file });
          },

          startUpload: () => {
            const machine = get().uploadMachine;
            machine.send({ type: 'START_UPLOAD' });
          },

          // 🎯 CONSOLIDATED: Primary progress update function
          updateUploadProgress: progress => {
            const machine = get().uploadMachine;
            machine.send({ type: 'UPLOAD_PROGRESS', progress });
          },

          cancelUpload: () => {
            const machine = get().uploadMachine;
            machine.send({ type: 'CANCEL' });
            // After a brief delay, mark as cancelled (simulates async cancellation)
            setTimeout(() => {
              machine.send({ type: 'CANCELLED' });
            }, 100);
          },

          completeUpload: data => {
            const machine = get().uploadMachine;
            machine.send({ type: 'COMPLETE', data });
          },

          errorUpload: error => {
            const machine = get().uploadMachine;
            machine.send({ type: 'ERROR', error });
          },

          retryUpload: () => {
            const machine = get().uploadMachine;
            machine.send({ type: 'RETRY' });
          },

          resetUpload: () => {
            const machine = get().uploadMachine;
            machine.send({ type: 'RESET' });
          },
        }; // End of return statement
      }, // End of persist callback
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
