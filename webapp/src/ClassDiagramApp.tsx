import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import ClassDiagramWorkspace from './ClassDiagramWorkspace';

// use emotion for CSS when ready
// https://emotion.sh/docs/introduction

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});

function ClassDiagramApp() {
  return (
    <ThemeProvider theme={darkTheme}>
      <ClassDiagramWorkspace />
    </ThemeProvider>
  );
}

export default ClassDiagramApp;