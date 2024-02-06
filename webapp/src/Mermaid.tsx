import React, { useEffect } from "react";
import mermaid from "mermaid";

export interface MermaidProps {
  diagram: string;
  name: string;
}

export const Mermaid: React.FC<MermaidProps> = ({ diagram, name }) => {
  const ref = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: true,
      securityLevel: "loose",
      theme: "forest",
      logLevel: 5
    });
    mermaid.contentLoaded();
  }, []);

  if (!diagram) return null;
  
  return (
    <div>
      <h2>This is it</h2>
      <div className="mermaid" key={name}>
        {diagram}
      </div>
    </div>
  );
};
