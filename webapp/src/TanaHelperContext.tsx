import mermaid from 'mermaid';
import React, { createContext, useMemo, useState } from 'react';

export const TanaHelperContext = createContext({
  graphData: undefined, setGraphData: (a)=>{},
  loading: false, setLoading: (a)=>{},
  mermaidText: undefined, setMermaidText: (a)=>{},
  twoDee: undefined, setTwoDee: (a)=>{},
});

export function TanaHelperContextProvider({ children }) {
  const [graphData, setGraphData] = useState();
  const [mermaidText, setMermaidText] = useState();
  const [loading, setLoading] = useState();
  const [twoDee, setTwoDee] = useState(false);

  const contextValue = useMemo(
    () => ({ 
      graphData, setGraphData, 
      loading, setLoading, 
      mermaidText, setMermaidText,
      twoDee, setTwoDee}),
    [graphData, loading, mermaidText, twoDee]
  );

  return (
    <TanaHelperContext.Provider value={contextValue}>
      {children}
    </TanaHelperContext.Provider>
  )
}