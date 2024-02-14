/*
  Graph Viz UI for tana-helper

  Built as a React app
*/

import React from "react";
import { createRoot } from "react-dom/client";
import { GlobalStyles } from "@mui/material";
import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import GraphWorkspace from "./GraphWorkspace";
import './Graph.css'

// import reportWebVitals from "./reportWebVitals";

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error('Failed to find the root element');

const root = createRoot(rootElement);

// use emotion for CSS when ready
// https://emotion.sh/docs/introduction

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});

root.render(
  <React.StrictMode>
    <CssBaseline />
    <GlobalStyles styles={{ body: { backgroundColor: 'black' } }} />
    <ThemeProvider theme={darkTheme}>
      <GraphWorkspace />
    </ThemeProvider>
  </React.StrictMode>
);

// reportWebVitals();