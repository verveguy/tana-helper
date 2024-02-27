import React from 'react';
import { CssBaseline, ListItemButton, ListItemText } from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { VisualizerContextProvider } from './VisualizerContext';
import { BrowserRouter, Link, MemoryRouter, NavLink, Route, Router, Routes } from 'react-router-dom';

import MainUI from './MainUI';
import Home from './Home';
import Logs from './Logs';
import ClassDiagramControls from './ClassDiagramControls';
import ClassDiagram from './components/ClassDiagram';
import Visualizer from './components/Visualizer';
import VisualizerControls from './VisualizerControls';
import API from './API';
import { text } from 'stream/consumers';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
  typography: {
    fontSize: 12,
  },
});

export default function App() {

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      {/* <SimpleMain /> */}
      <VisualizerContextProvider>
        <BrowserRouter>
          <MainUI
            navigation={[
              ['Home', '/ui'],
              ['API', '/ui/rapidoc'],
              ['Logs', '/ui/logs'],
              ['Class Diagram', '/ui/classdiagram'],
              ['Visualizer', '/ui/visualizer'],
              //['Configure', '/ui/configure'],
            ].map(([text, link], index) => (
              <li>
                <ListItemButton component={NavLink} to={link} selected={location.pathname == link}>
                  <ListItemText primary={text} />
                </ListItemButton>
              </li>
            ))}
            controls={[
              ['/ui/classdiagram', <ClassDiagramControls />],
              ['/ui/visualizer', <VisualizerControls />],
            ].map(([link, control], index) => (
              <Route path={link} element={control} />
            ))}
            contents={[
              ['/ui', <Home />],
              ['/ui/rapidoc', <API />],
              ['/ui/logs', <Logs />],
              ['/ui/classdiagram', <ClassDiagram />],
              ['/ui/visualizer', <Visualizer />],
              //['/ui/configure', <Configure />],
              ['*', <Home />],
            ].map(([link, view], index) => (
              <Route path={link} element={view} />
            ))}
          />
        </BrowserRouter>
      </VisualizerContextProvider>
    </ThemeProvider >
  );
}