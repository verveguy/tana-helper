import React, { createContext, useMemo, useState } from 'react';

export const TanaHelperContext = createContext({
  graphData: undefined, setGraphData: (a)=>{},
  loading: false, setLoading: (a)=>{},
  mermaidText: undefined, setMermaidText: (a)=>{},
  ragIndexData: undefined, setRagIndexData: (a)=>{},
  obsidianExportData: undefined, setObsidianExportData: (a)=>{},
  config: undefined, setConfig: (a)=>{},
  webhooks: undefined, setWebhooks: (a)=>{},
  twoDee: false, setTwoDee: (a)=>{},
});

export function TanaHelperContextProvider({ children }) {
  const [graphData, setGraphData] = useState();
  const [mermaidText, setMermaidText] = useState();
  const [loading, setLoading] = useState(false);
  const [ragIndexData, setRagIndexData] = useState();
  const [obsidianExportData, setObsidianExportData] = useState();
  const [config, setConfig] = useState();
  const [webhooks, setWebhooks] = useState();
  const [twoDee, setTwoDee] = useState(false);

  const contextValue = useMemo(
    () => ({ 
      graphData, setGraphData, 
      loading, setLoading, 
      mermaidText, setMermaidText,
      ragIndexData, setRagIndexData,
      obsidianExportData, setObsidianExportData,
      config, setConfig,
      webhooks, setWebhooks,
      twoDee, setTwoDee}),
    [graphData, loading, mermaidText, ragIndexData, obsidianExportData, config, webhooks, twoDee]
  );

  return (
    <TanaHelperContext.Provider value={contextValue}>
      {children}
    </TanaHelperContext.Provider>
  )
}