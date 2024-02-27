import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import MenuIcon from '@mui/icons-material/Menu';
import MuiAppBar, { AppBarProps as MuiAppBarProps } from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Drawer from '@mui/material/Drawer';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import { styled, useTheme } from '@mui/material/styles';
import React, { ReactNode } from "react";

import { Link, Route, Routes, useLocation } from "react-router-dom";
import ClassDiagramControls from './ClassDiagramControls';
import Configure from "./Configure";
import Home from "./Home";
import Logs from "./Logs";
import VisualizerControls from './VisualizerControls';
import ClassDiagram from "./components/ClassDiagram";
import Visualizer from "./components/Visualizer";

import { Paper } from '@mui/material';
import './MainUI.css';

// pass in the routes here
// Title, link, view, controls
// TODO: make these into some kind of JSX children
interface MainUIProps {
  routes: [string, string, ReactNode, ReactNode][];
}

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


export default function MainUI(props:MainUIProps) {
  const { routes } = props;
  const theme = useTheme();
  const [open, setOpen] = React.useState(false);
  const location = useLocation();

  const handleDrawerOpen = () => {
    setOpen(true);
  };

  const handleDrawerClose = () => {
    setOpen(false);
  };

  return (

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
        <div className='nav-controls'>
          <Paper elevation={0}>
            <List aria-label="main mailbox folders">
              {routes.map(([text, link, view, controls ], index) => (
                <li>
                  <ListItemButton component={Link} to={link} selected={location.pathname == link}>
                    <ListItemText primary={text} />
                  </ListItemButton>
                </li>
              ))}
            </List>
          </Paper>
        </div>
        <Divider />
        <div id="controls">
          <Routes>
          {routes.map(([text, link, view, controls ], index) => (
            <Route path={link} element={controls} />

          ))}
          </Routes>
        </div>
      </Drawer>
      {/* TODO: Adjust width here on Main component*/}
      <Main open={open} style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* <DrawerHeader style={{height: 'auto'}}/> */}
        <DrawerHeader />
        <div className="content">
          <Routes>
          {routes.map(([text, link, view, controls ], index) => (
            <Route path={link} element={view} />

          ))}
          </Routes>
        </div>
      </Main>
    </Box>
  );
}
