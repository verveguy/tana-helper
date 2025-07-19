/*
  Live logs viewer using xterm.js terminal
  Connects to the WebSocket log stream endpoint
*/

import React, { useEffect, useRef, useCallback } from "react";
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
import './Logs.css';
import { useDimensions } from "./utils";

export default function Logs() {
  const containerRef = useRef<HTMLDivElement>(null);
  const dimensions = useDimensions(containerRef);
  const termRef = useRef<HTMLDivElement>(null);
  const terminalRef = useRef<Terminal | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Initialize terminal when component mounts
  useEffect(() => {
    if (!termRef.current) return;

    // Create terminal instance
    const terminal = new Terminal({
      cursorBlink: false,
      fontSize: 12,
      fontFamily: 'Monaco, Menlo, "DejaVu Sans Mono", monospace',
      theme: {
        background: '#1a1a1a',
        foreground: '#ffffff'
      }
    });
    
    const fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);

    // Open terminal in the DOM element
    terminal.open(termRef.current);
    fitAddon.fit();

    // Store references
    terminalRef.current = terminal;
    fitAddonRef.current = fitAddon;

    // Initialize WebSocket connection
    const ws = new WebSocket("ws://localhost:8000/ws/log");
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected for log streaming");
      terminal.writeln("Connected to log stream...\r\n");
    };

    ws.onmessage = (event) => {
      if (terminalRef.current) {
        terminalRef.current.write(event.data);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      if (terminalRef.current) {
        terminalRef.current.writeln("\r\nDisconnected from log stream.");
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      if (terminalRef.current) {
        terminalRef.current.writeln("\r\nError connecting to log stream.");
      }
    };

    // Cleanup function
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (terminalRef.current) {
        terminalRef.current.dispose();
      }
    };
  }, []);

  // Handle window resizing
  useEffect(() => {
    if (!dimensions || !fitAddonRef.current) return;
    
    const resizeTimeout = setTimeout(() => {
      if (fitAddonRef.current) {
        fitAddonRef.current.fit();
      }
    }, 100);

    return () => clearTimeout(resizeTimeout);
  }, [dimensions]);

  return (
    <div className="terminal-container" ref={containerRef}>
      <div className="log-container">
        <div id="terminal" ref={termRef} />
      </div>
    </div>
  );
}
