import React, { useEffect } from "react";
import mermaid from "mermaid";

export interface MermaidProps {
  diagram: string;
  id: string;
  style?: {};
}

export const Mermaid: React.FC<MermaidProps> = ({ diagram, id, style }) => {
  const ref = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: true,
      securityLevel: "loose",
      theme: "dark",
      logLevel: 5
    });
    // mermaid.contentLoaded();
  }, []);

  useEffect(() => {
    document.getElementById(id)?.removeAttribute("data-processed");
    mermaid.contentLoaded();
  }, [diagram]);

  if (!diagram) return null;

  return (
    <div className="mermaid" id={id} style={style} >
      {diagram}
    </div>
  );
};
