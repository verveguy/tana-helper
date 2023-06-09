/*
  Graph Viz UI for tana-helper

  Built as a React app
*/

import React from "react";
import { createRoot } from "react-dom/client";
import { GlobalStyles } from "@mui/material";
import CssBaseline from '@mui/material/CssBaseline';
import GraphWorkspace from "./GraphWorkspace";
import GraphApp from "./GraphApp";
// import reportWebVitals from "./reportWebVitals";

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error('Failed to find the root element');

const root = createRoot(rootElement);
root.render(
  <React.StrictMode>
    <CssBaseline />
    <GlobalStyles styles={{ body: { backgroundColor: 'black' } }} />
    <GraphApp />
  </React.StrictMode>
);

// reportWebVitals();