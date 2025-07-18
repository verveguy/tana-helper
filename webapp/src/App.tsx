import React from 'react';
import { BrowserRouter, NavLink, Route, useLocation } from 'react-router-dom';

import ClassDiagramControls from './components/ClassDiagramControls';
import Home from './components/Home';
import Logs from './components/Logs';
import UILayout from './UILayout';
import VisualizerControls from './components/VisualizerControls';
import ClassDiagram from './components/ClassDiagram';
import Visualizer from './components/Visualizer';
import RAGIndex from './components/RAGIndex';
import RAGIndexControls from './components/RAGIndexControls';
import Api from './components/Api';
import Configure from './components/Configure';

export default function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <BrowserRouter>
        <Panels />
      </BrowserRouter>
    </div>
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
    label: 'Class Diagram',
    link: '/ui/diagram',
    key: 'classdiagram',
    content: <ClassDiagram />,
    control: <ClassDiagramControls />
  },
  {
    label: 'Visualizer',
    link: '/ui/visualizer',
    key: 'visualizer',
    content: <Visualizer />,
    control: <VisualizerControls />
  },
  {
    label: 'RAG Index',
    link: '/ui/ragindex',
    key: 'ragindex',
    content: <RAGIndex />,
    control: <RAGIndexControls />
  },
  {
    label: 'API Documentation',
    link: '/ui/api',
    key: 'api',
    content: <Api />,
    control: null
  },
  {
    label: 'Configure',
    link: '/ui/configure',
    key: 'configure',
    content: <Configure />,
    control: null
  },
  {
    label: 'Logs',
    link: '/ui/logs',
    key: 'logs',
    content: <Logs />,
    control: null
  }
];

function Panels() {
  const location = useLocation();

  const menuItems = config.map((entry) => (
    <NavLink
      to={entry.link}
      key={entry.key}
      className={({ isActive }) =>
        `flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors ${
          isActive
            ? 'bg-primary text-primary-foreground'
            : 'text-muted-foreground hover:text-foreground hover:bg-accent'
        }`
      }
    >
      {entry.label}
    </NavLink>
  ));

  const routes = config.map((entry) => (
    <Route 
      key={entry.key} 
      path={entry.link} 
      element={
        <UILayout 
          content={entry.content} 
          control={entry.control} 
        />
      } 
    />
  ));

  return (
    <UILayout 
      menuItems={menuItems} 
      routes={routes}
    />
  );
}

