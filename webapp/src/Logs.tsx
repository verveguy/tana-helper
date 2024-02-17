/*
  Log Viewer UI for tana-helper

  Built as a React app
*/
import React, { StrictMode } from 'react';
import { createRoot } from "react-dom/client";
import { GlobalStyles } from "@mui/material";
import CssBaseline from '@mui/material/CssBaseline';
import TanaHelperLogViewer from "./TanaHelperLogViewer";
import { ThemeProvider, createTheme } from '@mui/material/styles';

import './Logs.css';

// import reportWebVitals from "./reportWebVitals";

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error('Failed to find the root element');

const root = createRoot(rootElement);

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});

root.render(
  // <StrictMode>
    <ThemeProvider theme={darkTheme}>
      <TanaHelperLogViewer />
    </ThemeProvider>
  // </StrictMode>
);

// reportWebVitals();