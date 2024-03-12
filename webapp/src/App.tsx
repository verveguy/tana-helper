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

const config = [
  {
    label: 'Home',
    link: '/ui',
    key: 'home',
    content: <Home />,
    control: null
  },
  {
    label: 'API',
    link: '/ui/api',
    key: 'api',
    content: <API />,
    control: null
  },
  {
    label: 'Logs',
    link: '/ui/logs',
    key: 'logs',
    content: <Logs />,
    control: null
  },
  {
    label: 'Tag Diagram',
    link: '/ui/tagdiagram',
    key: 'tagdiagram',
    content: <ClassDiagram />,
    control: <ClassDiagramControls />
  },
  {
    label: 'Visualizer',
    link: '/ui/visualizer',
    key: 'visualizer',
    content: <Visualizer />,
    control: <VisualizerControls />
  }
];

function Panels() {
  const location = useLocation();

  return (
    <UILayout
      navigation={config.map(({ label, link, key }, index) => (
          <ListItemButton key={key} component={NavLink} to={link} selected={location.pathname == link}>
            <ListItemText key={key} primary={label} />
          </ListItemButton>
        ))}
      controls={config.map(({ link, control, key }, index) => {
        if (control != null) {
          return <Route key={key} path={link} element={control} />
        }
        else {
          return null;
        }
      })}
      contents={config.map(({ link, content, key }, index) => (
        <Route key={key} path={link} element={content} />
      ))}
      />
  )
}

