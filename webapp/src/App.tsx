import React from 'react';

import { CssBaseline, ListItemButton, ListItemText } from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { BrowserRouter, NavLink, Route, useLocation } from 'react-router-dom';
import { TanaHelperContextProvider } from './TanaHelperContext';

import API from './API';
import ClassDiagramControls from './ClassDiagramControls';
import Home from './Home';
import Logs from './Logs';
import UILayout from './UILayout';
import VisualizerControls from './VisualizerControls';
import ClassDiagram from './components/ClassDiagram';
import Visualizer from './components/Visualizer';

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
      <TanaHelperContextProvider>
        <BrowserRouter>
          <Panels />
        </BrowserRouter>
      </TanaHelperContextProvider>
    </ThemeProvider >
  );
}

function Panels() {
  const location = useLocation();

  return (
    <UILayout
      navigation={[
        ['Home', '/ui', 'home'],
        ['API', '/ui/rapidoc', 'api'],
        ['Logs', '/ui/logs', 'logs'],
        ['Class Diagram', '/ui/classdiagram', 'classdiagram'],
        ['Visualizer', '/ui/visualizer', 'visualizer'],
        //['Configure', '/ui/configure', 'configure'],
      ].map(([text, link, key], index) => (
        <li>
          <ListItemButton key={key} component={NavLink} to={link} selected={location.pathname == link}>
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
  )
}

