/*
  This is a React based app which is the Configuration page
  for tana-helper

  Right now, it lets you configure schemas for webhooks
  
*/

import React, { useEffect, useRef, useState } from "react";
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
/* This CSS might be unecessary ... see https://github.com/xtermjs/xterm.js/issues/3564 */
import './TanaHelperLogViewer.css';
import { width } from "@mui/system";


let terminal;
let fitAddon;

/* useWindowSize lets us track changes in window size and capture new dimensions */

function useWindowSize() {
  // Initialize state with undefined width/height so server and client renders match
  // Learn more here: https://joshwcomeau.com/react/the-perils-of-rehydration/
  const [windowSize, setWindowSize] = useState({
    width: undefined,
    height: undefined
  });

  useEffect(() => {
    // Handler to call on window resize
    function handleResize() {
      // Set window width/height to state
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
      console.log("handled resize", window.innerHeight, window.innerWidth)
    }

    // Add event listener
    window.addEventListener("resize", handleResize);

    // Call handler right away so state gets updated with initial window size
    handleResize();

    // Remove event listener on cleanup
    return () => window.removeEventListener("resize", handleResize);
  }, []); // Empty array ensures that effect is only run on mount

  return windowSize;
}

const TanaHelperLogViewer = () => {
  const { width, height } = useWindowSize();
  const term_ref = useRef(null);

  // once we have a term-ref, we can create the terminal component
  // and start listening for log records
  useEffect(() => {
    terminal = new Terminal();
    fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);

    terminal.open(term_ref?.current);
    fitAddon.fit();

    const ws_log = new WebSocket("ws://localhost:8000/ws/log");

    ws_log.onmessage = function (event) {
      console.log("Got more data")
      terminal.write(event.data + '\r')
    };
  }, [term_ref]);

  // Whenever size changes, fit the terminal to the new height
  useEffect(() => {
    if (height === undefined || width == undefined) return;
    console.log("Refit terminal to new height", height)
    fitAddon.fit();
  }, [height, width]);

  return (
    // <div className="TanaHelperLogViewer">
      <div className="terminal-container">
        <div id="terminal" ref={term_ref} />
      </div>
    // </div>
  );
}
export default TanaHelperLogViewer;
