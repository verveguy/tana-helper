import mermaid from 'mermaid';
import React, { createContext, useMemo, useState } from 'react';

export const VisualizerContext = createContext({
  graphData: undefined, setGraphData: undefined,
  loading: false, setLoading: undefined,
  mermaidText: "", setMermaidText: undefined,
});


export function VisualizerContextProvider({ children }) {
  const [graphData, setGraphData] = useState();
  const [mermaidText, setMermaidText] = useState();
  const [loading, setLoading] = useState();

  const contextValue = useMemo(
    () => ({ graphData, setGraphData, loading, setLoading, mermaidText, setMermaidText }),
    [graphData, loading, mermaidText]
  );

  return (
    <VisualizerContext.Provider value={contextValue}>
      {children}
    </VisualizerContext.Provider>
  )
}