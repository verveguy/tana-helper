import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import MenuIcon from '@mui/icons-material/Menu';
import MuiAppBar, { AppBarProps as MuiAppBarProps } from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import CssBaseline from '@mui/material/CssBaseline';
import Divider from '@mui/material/Divider';
import Drawer from '@mui/material/Drawer';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import { styled, useTheme } from '@mui/material/styles';
import React, { useMemo, useRef } from "react";

import { BrowserRouter, Link, NavLink, Route, Routes } from "react-router-dom";
import ClassDiagram from "./components/ClassDiagram";
import Configure from "./Configure";
import Home from "./Home";
import Logs from "./Logs";
import Visualizer from "./components/Visualizer";
import VisualizerControls from './VisualizerControls';
import { VisualizerContext, VisualizerContextProvider } from './VisualizerContext';
import ClassDiagramControls from './ClassDiagramControls';

import './MainUI.css';
import { Button, Paper } from '@mui/material';

// TODO: can this be dynamic based on content?
const drawerWidth = 150;

const Main = styled('main', { shouldForwardProp: (prop) => prop !== 'open' })<{
  open?: boolean;
}>(({ theme, open }) => ({
  flexGrow: 1,
  padding: theme.spacing(1),
  transition: theme.transitions.create('margin', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  marginLeft: `-${drawerWidth}px`,
  ...(open && {
    transition: theme.transitions.create('margin', {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
    marginLeft: 0,
  }),
  height: '100%',
}));

interface AppBarProps extends MuiAppBarProps {
  open?: boolean;
}

const AppBar = styled(MuiAppBar, {
  shouldForwardProp: (prop) => prop !== 'open',
})<AppBarProps>(({ theme, open }) => ({
  transition: theme.transitions.create(['margin', 'width'], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  ...(open && {
    width: `calc(100% - ${drawerWidth}px)`,
    marginLeft: `${drawerWidth}px`,
    transition: theme.transitions.create(['margin', 'width'], {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
  }),
}));

const DrawerHeader = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  padding: theme.spacing(0, 1),
  // necessary for content to be below app bar
  ...theme.mixins.toolbar,
  justifyContent: 'flex-end',
}));


export default function MainUI() {
  const theme = useTheme();
  const [open, setOpen] = React.useState(false);

  const handleDrawerOpen = () => {
    setOpen(true);
  };

  const handleDrawerClose = () => {
    setOpen(false);
  };

  return (
    // <VisualizerContext.Provider value={contextValue}>
    <VisualizerContextProvider>
      <BrowserRouter>
        <Box sx={{ display: 'flex' }} style={{ height: '100%' }}>
          <AppBar position="fixed" open={open}>
            <Toolbar>
              <IconButton
                color="inherit"
                aria-label="open drawer"
                onClick={handleDrawerOpen}
                edge="start"
                sx={{ mr: 2, ...(open && { display: 'none' }) }}
              >
                <MenuIcon />
              </IconButton>
              <Typography variant="h6" noWrap component="div">
                Tana Helper
              </Typography>
            </Toolbar>
          </AppBar>
          <Drawer
            sx={{
              width: drawerWidth,
              flexShrink: 0,
              '& .MuiDrawer-paper': {
                width: drawerWidth,
                boxSizing: 'border-box',
              },
            }}
            variant="persistent"
            anchor="left"
            open={open}
          >
            <DrawerHeader>
              <IconButton onClick={handleDrawerClose}>
                {theme.direction === 'ltr' ? <ChevronLeftIcon /> : <ChevronRightIcon />}
              </IconButton>
            </DrawerHeader>
            <Divider />
            {/* <List>
              {[
                ['Home', '/ui'],
                ['Configure', '/ui/configure'],
                ['Logs', '/ui/logs'],
                ['Class Diagram', '/ui/classdiagram'],
                ['Visualizer', '/ui/visualizer'],
              ].map(([text, link], index) => (
                <ListItem key={text} disablePadding>
                  <ListItemButton>
                    <NavLink to={link}><ListItemText primary={text} /></NavLink>
                  </ListItemButton>
                </ListItem>
              ))}
            </List> */}
            <div className='nav-controls'>
              <Paper elevation={0}>
                <List aria-label="main mailbox folders">
                  {[
                    ['Home', '/ui'],
                    ['Logs', '/ui/logs'],
                    ['Class Diagram', '/ui/classdiagram'],
                    ['Visualizer', '/ui/visualizer'],
                    ['Configure', '/ui/configure'],
                  ].map(([text, link], index) => (
                    <li><ListItem button component={Link} to={link}>
                      <ListItemText primary={text} />
                      {/* <Button component={Link} to={link}>{text}</Button> */}
                    </ListItem>
                    </li>
                  ))}
                </List>
              </Paper>
            </div>
            <Divider />
            <div id="controls">
              <Routes>
                <Route path="/ui" element={<div />} />
                <Route path="/ui/configure" element={<div />} />
                <Route path="/ui/logs" element={<div />} />
                <Route path="/ui/classdiagram" element={<ClassDiagramControls />} />
                <Route path="/ui/visualizer" element={<VisualizerControls />} />
              </Routes>
            </div>
          </Drawer>
          {/* TODO: Adjust width here on Main component*/}
          <Main open={open} style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* <DrawerHeader style={{height: 'auto'}}/> */}
            <DrawerHeader />
            <div className="content">
              <Routes>
                <Route path="/ui" element={<Home />} />
                <Route path="/ui/configure" element={<Configure />} />
                <Route path="/ui/logs" element={<Logs />} />
                <Route path="/ui/classdiagram" element={<ClassDiagram />} />
                <Route path="/ui/visualizer" element={<Visualizer leftDrawerSpace={open ? drawerWidth : 0} />} />
              </Routes>
            </div>
          </Main>
        </Box>
      </BrowserRouter >
    </VisualizerContextProvider >
    // </VisualizerContext.Provider>
  );
}
