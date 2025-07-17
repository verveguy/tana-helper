/*

  Visualize a Tana workspace tags as a class diagram.

*/

import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, Typography } from '@mui/material';
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
            <div style="color: red; padding: 20px;">
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
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Class Diagram
          </Typography>
          <Typography>Loading diagram...</Typography>
        </CardContent>
      </Card>
    );
  }

  if (!mermaidText) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Class Diagram
          </Typography>
          <Typography color="textSecondary">
            No diagram data available. Use the controls to generate a diagram.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Class Diagram
        </Typography>
        <div 
          ref={mermaidRef}
          style={{ 
            width: '100%', 
            minHeight: '200px',
            display: 'flex',
            justifyContent: 'center',
            alignItems: diagramRendered ? 'flex-start' : 'center'
          }}
        >
          {!diagramRendered && !loading && mermaidText && (
            <Typography>Rendering diagram...</Typography>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

