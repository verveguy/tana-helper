// React import not needed for JSX in React 17+
import { BrowserRouter, NavLink, Route, Routes, useLocation } from 'react-router-dom';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from './components/ui/button';
import { useSidebarCollapsed, useAppActions } from './hooks/useAppStore';

import ClassDiagramControls from './components/ClassDiagramControls';
import Home from './components/Home';
import Logs from './components/Logs';
import VisualizerControls from './components/VisualizerControls';
import ClassDiagram from './components/ClassDiagram';
import Visualizer from './components/Visualizer';
import RAGIndex from './components/RAGIndex';
import RAGIndexControls from './components/RAGIndexControls';
import ObsidianExport from './components/ObsidianExport';
import ObsidianExportControls from './components/ObsidianExportControls';
import Api from './components/Api';
import Configure from './components/Configure';

export default function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <BrowserRouter basename="/ui">
        <Panels />
      </BrowserRouter>
    </div>
  );
}

const config = [
  {
    label: 'Home',
    link: '/',
    key: 'home',
    content: <Home />,
    control: null,
  },
  {
    label: 'Class Diagram',
    link: '/diagram',
    key: 'classdiagram',
    content: <ClassDiagram />,
    control: <ClassDiagramControls />,
  },
  {
    label: 'Visualizer',
    link: '/visualizer',
    key: 'visualizer',
    content: <Visualizer />,
    control: <VisualizerControls />,
  },
  {
    label: 'RAG Index',
    link: '/ragindex',
    key: 'ragindex',
    content: <RAGIndex />,
    control: <RAGIndexControls />,
  },
  {
    label: 'Obsidian Export',
    link: '/obsidian',
    key: 'obsidian',
    content: <ObsidianExport />,
    control: <ObsidianExportControls />,
  },
  {
    label: 'API Documentation',
    link: '/api',
    key: 'api',
    content: <Api />,
    control: null,
  },
  {
    label: 'Configure',
    link: '/configure',
    key: 'configure',
    content: <Configure />,
    control: null,
  },
  {
    label: 'Logs',
    link: '/logs',
    key: 'logs',
    content: <Logs />,
    control: null,
  },
];

function Panels() {
  const location = useLocation();
  const sidebarCollapsed = useSidebarCollapsed();
  const { setSidebarCollapsed } = useAppActions();

  const toggleSidebar = () => setSidebarCollapsed(!sidebarCollapsed);

  const menuItems = config.map(entry => (
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
      title={entry.label}
    >
      {sidebarCollapsed ? entry.label.charAt(0) : entry.label}
    </NavLink>
  ));

  // Find the current route config based on location
  const currentRoute = config.find(entry => entry.link === location.pathname);

  const routes = config.map(entry => (
    <Route key={entry.key} path={entry.link} element={entry.content} />
  ));

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <div
        className={`relative flex flex-col bg-card border-r border-border h-full overflow-hidden transition-all duration-300 ease-in-out ${
          sidebarCollapsed ? 'w-16' : 'w-60'
        }`}
      >
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-4 border-b border-border flex-shrink-0">
          {!sidebarCollapsed && (
            <h1 className="text-xl font-semibold text-foreground">Tana Helper</h1>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className={sidebarCollapsed ? 'mx-auto' : 'ml-auto'}
          >
            {sidebarCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Scrollable Sidebar Content */}
        <div className="flex-1 overflow-y-auto">
          {/* Navigation */}
          <nav className="p-4">
            <div className="space-y-2">{menuItems}</div>
          </nav>

          {/* Controls Section - Show controls for current route */}
          {!sidebarCollapsed && currentRoute?.control && (
            <div className="border-t border-border p-4">
              <div className="text-sm font-medium text-muted-foreground mb-2">Controls</div>
              {currentRoute.control}
            </div>
          )}
        </div>
      </div>

      {/* Main Content - Fixed position, fills remaining space */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Content Area - Full height, no padding for visualizations */}
        <main className="flex-1 h-full w-full overflow-hidden">
          <Routes>{routes}</Routes>
        </main>
      </div>
    </div>
  );
}
