/*

  Visualize a Tana workspace tags as a class diagram.

*/

import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Loader2 } from 'lucide-react';
import mermaid from 'mermaid';

// Replace context with Zustand store
import { useMermaidText, useClassLoading, useClassError } from "../hooks/useAppStore";

export default function ClassDiagram() {
  // Use Zustand hooks instead of context  
  const mermaidText = useMermaidText();
  const loading = useClassLoading();
  const error = useClassError();
  
  const [renderedSvg, setRenderedSvg] = useState<string>('');
  const [diagramRendered, setDiagramRendered] = useState(false);

  useEffect(() => {
    mermaid.initialize({ 
      startOnLoad: true,
      theme: 'dark',
      securityLevel: 'loose',
    });
  }, []);

  useEffect(() => {
    if (mermaidText && !loading) {
      const renderDiagram = async () => {
        try {
          setDiagramRendered(false);
          setRenderedSvg('');
          
          const { svg } = await mermaid.render('mermaid-diagram-' + Date.now(), mermaidText);
          setRenderedSvg(svg);
          setDiagramRendered(true);
        } catch (error) {
          console.error('Mermaid rendering error:', error);
          const errorHtml = `
            <div class="text-red-400 p-5 text-center">
              Error rendering diagram: ${error instanceof Error ? error.message : 'Unknown error'}
            </div>
          `;
          setRenderedSvg(errorHtml);
          setDiagramRendered(true);
        }
      };

      renderDiagram();
    }
  }, [mermaidText, loading]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full w-full bg-background">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="text-lg">Generating class diagram...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full w-full bg-background">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Class Diagram Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!mermaidText) {
    return (
      <div className="flex items-center justify-center h-full w-full bg-background">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>Class Diagram</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center text-muted-foreground py-8">
              <div className="space-y-2">
                <div className="text-lg">No diagram data available</div>
                <div className="text-sm">
                  Use the controls to generate a class diagram from your Tana data.
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="relative h-full w-full bg-background overflow-auto">
      {/* Title overlay */}
      <div className="absolute top-4 left-4 z-10 bg-background/90 px-3 py-2 rounded-lg border border-border shadow-lg">
        <h2 className="text-lg font-semibold text-foreground">
          Class Diagram
        </h2>
        <p className="text-sm text-muted-foreground">
          Visual representation of your Tana data structure
        </p>
      </div>

      {/* Full-screen diagram container */}
      <div className="h-full w-full p-4 pt-20">
        {!diagramRendered && !loading && mermaidText && (
          <div className="w-full h-full flex justify-center items-center" style={{ minHeight: 'calc(100vh - 120px)' }}>
            <div className="flex items-center space-x-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Rendering diagram...</span>
            </div>
          </div>
        )}
        
        {diagramRendered && (
          <div 
            className="w-full h-full flex justify-center items-start overflow-auto"
            style={{ minHeight: 'calc(100vh - 120px)' }}
            dangerouslySetInnerHTML={{ __html: renderedSvg }}
          />
        )}
      </div>
    </div>
  );
}

