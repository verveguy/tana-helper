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
      theme: "dark",
      logLevel: 5
    });
    mermaid.contentLoaded();
  }, []);

  if (!diagram) return null;

  return (
    <div className="mermaid" key={name}>
      {diagram}
    </div>
  );
};
