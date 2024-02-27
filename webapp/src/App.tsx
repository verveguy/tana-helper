import React from 'react';
import { CssBaseline } from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { VisualizerContextProvider } from './VisualizerContext';
import { BrowserRouter } from 'react-router-dom';

import MainUI from './MainUI';
import Home from './Home';
import Logs from './Logs';
import ClassDiagramControls from './ClassDiagramControls';
import ClassDiagram from './components/ClassDiagram';
import Visualizer from './components/Visualizer';
import VisualizerControls from './VisualizerControls';
import API from './API';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});

export default function App() {

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      {/* <SimpleMain /> */}
      <VisualizerContextProvider>
        <BrowserRouter>
          <MainUI routes={
            [
              ['Home', '/ui', <Home />, <div />],
              ['API', '/rapidoc', <API />, <div />],
              ['Logs', '/ui/logs', <Logs />, <div />],
              ['Class Diagram', '/ui/classdiagram', <ClassDiagram />, <ClassDiagramControls />],
              ['Visualizer', '/ui/visualizer', <Visualizer />, <VisualizerControls />],
              //['Configure', '/ui/configure', <Configure />, <div/>],
            ]
          } />
        </BrowserRouter>
      </VisualizerContextProvider>
    </ThemeProvider>
  );
}