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
import './Logs.css';
import useWindowSize from "./components/utils";

let terminal;
let fitAddon;

export default function Logs() {
  const { windowWidth, windowHeight } = useWindowSize();
  const term_ref = useRef(null);
  let ws_log;

  useEffect(() => {
    ws_log = new WebSocket("ws://localhost:8000/ws/log");
    console.log("Created websocket")
  }, []);

  // once we have a term-ref, we can create the terminal component
  // and start listening for log records
  useEffect(() => {
    terminal = new Terminal();
    fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);

    terminal.open(term_ref?.current);
    fitAddon.fit();

    if (ws_log) {
      ws_log.onmessage = function (event) {
        console.log("Got more data")
        terminal.write(event.data + '\r')
      };
      console.log("Aded handler")
    }

    return (() => {ws_log.close(); console.log("Closed websocket")})
  }, [term_ref]);

  // Whenever size changes, fit the terminal to the new height
  useEffect(() => {
    if (windowHeight === undefined || windowWidth == undefined) return;
    console.log("Refit terminal to new height", windowHeight)
    fitAddon.fit();
  }, [windowHeight, windowWidth]);

  return (
    <div className="terminal-container">
      <div id="terminal" ref={term_ref} />
    </div>
  );
}
