/*
  Log Viewer UI for tana-helper

  Built as a React app
*/
import { ThemeProvider, createTheme } from '@mui/material/styles';
import React from 'react';
import { createRoot } from "react-dom/client";
import SimpleMain from './SimpleMain';
import './Root.css';  
import MainUI from './MainUI';
import { CssBaseline } from '@mui/material';

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
      <CssBaseline />
      {/* <SimpleMain /> */}
      <MainUI />
    </ThemeProvider>
  // </StrictMode>
);
