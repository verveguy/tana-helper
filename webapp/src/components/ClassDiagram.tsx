/*

  Visualize a Tana workspace tags as a class diagram.

*/

import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import mermaid from 'mermaid';

// Replace context with Zustand store
import { useMermaidText, useLoading } from "../hooks/useAppStore";

export default function ClassDiagram() {
  // Use Zustand hooks instead of context  
  const mermaidText = useMermaidText();
  const loading = useLoading();
  
  const mermaidRef = useRef<HTMLDivElement>(null);
  const [diagramRendered, setDiagramRendered] = useState(false);

  useEffect(() => {
    mermaid.initialize({ 
      startOnLoad: true,
      theme: 'dark',
      securityLevel: 'loose',
    });
  }, []);

  useEffect(() => {
    if (mermaidText && mermaidRef.current && !loading) {
      const renderDiagram = async () => {
        try {
          setDiagramRendered(false);
          mermaidRef.current!.innerHTML = '';
          
          const { svg } = await mermaid.render('mermaid-diagram', mermaidText);
          mermaidRef.current!.innerHTML = svg;
          setDiagramRendered(true);
        } catch (error) {
          console.error('Mermaid rendering error:', error);
          mermaidRef.current!.innerHTML = `
            <div class="text-destructive p-5 text-center">
              Error rendering diagram: ${error instanceof Error ? error.message : 'Unknown error'}
            </div>
          `;
        }
      };

      renderDiagram();
    }
  }, [mermaidText, loading]);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Class Diagram</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center min-h-[200px] text-muted-foreground">
            Loading diagram...
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!mermaidText) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Class Diagram</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-8">
            No diagram data available. Use the controls to generate a diagram.
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Class Diagram</CardTitle>
        <CardDescription>
          Visual representation of your Tana data structure
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div 
          ref={mermaidRef}
          className={`w-full min-h-[200px] flex justify-center ${
            diagramRendered ? 'items-start' : 'items-center'
          }`}
        >
          {!diagramRendered && !loading && mermaidText && (
            <div className="text-muted-foreground">Rendering diagram...</div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

