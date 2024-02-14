/*
  This is a React based app which is the Configuration page
  for tana-helper

  Right now, it lets you configure schemas for webhooks
  
*/

import React, { useEffect, useRef } from "react";
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
/* This CSS might be unecessary ... see https://github.com/xtermjs/xterm.js/issues/3564 */
import './TanaHelperLogViewer.css';

const TanaHelperLogViewer = () => {
  const term_ref = useRef(null);

  useEffect(() => {
    const term = new Terminal();
    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);

    if (term_ref?.current != null) {
      term.open(term_ref?.current);
      fitAddon.fit();
    }

    const ws_log = new WebSocket("ws://localhost:8000/ws/log");

    ws_log.onmessage = function (event) {
      console.log("Got more data")
      term.write(event.data + '\r')
    };

    window.onresize = function () {
      fitAddon.fit();
    };
  }, []);

  return (
    <div id="terminal" ref={term_ref} />
  );
}
export default TanaHelperLogViewer;
