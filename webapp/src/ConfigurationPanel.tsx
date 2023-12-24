/*
  This is a React based app which is the Configuration page
  for tana-helper

  Right now, it lets you configure schemas for webhooks
  
*/

import React, { useEffect, useState } from "react";
import { FormControlLabel, FormGroup, Switch, TextField } from "@mui/material";
import axios from 'axios';

import React, { SyntheticEvent, useCallback, useEffect, useRef, useState } from "react";
import { styled, useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import CssBaseline from '@mui/material/CssBaseline';
import MuiAppBar, { AppBarProps as MuiAppBarProps } from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ForceGraph3D, { GraphData } from 'react-force-graph-3d';
// import ForceGraph2D, { GraphData } from 'react-force-graph-2d';
import { Button, Checkbox, CircularProgress, FormControlLabel, FormGroup, Grid, TextField } from '@mui/material';
import axios from 'axios';
import { Container } from "@mui/system";
import { useWindowSize } from "@react-hook/window-size";
import { Id, Index } from "flexsearch-ts";


const ConfigurationPanel = () => {

  const [schemas, setSchemas] = useState([]);

  useEffect(() => {
    axios.get('/schema')
      .then(response => {
        setSchemas(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  }, []);

  return (
    <ul>
      {schemas.map(schema => (
        <li key={schema}>{schema}</li>
      ))}
    </ul>
  );
}



const drawerWidth = 240;

const Main = styled('main', { shouldForwardProp: (prop) => prop !== 'open' })<{
  open?: boolean;
}>(({ theme, open }) => ({
  flexGrow: 1,
  padding: theme.spacing(3),
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


export default function GraphWorkspace() {
  const theme = useTheme();
  const [open, setOpen] = useState(true);
  const [config, setConfig] = useState<GraphConfig>();

  const handleDrawerOpen = () => {
    setOpen(true);
  };

  const handleDrawerClose = () => {
    setOpen(false);
  };

  function handleShowAllNodes(event: SyntheticEvent<Element, Event>, checked: boolean): void {
    let new_config = { ...config } as GraphConfig;
    new_config.include_all_nodes = checked;
    setConfig(new_config);
  }


  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
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
            TanaHelper Configuration
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
        <Box style={{ padding: 10, marginLeft: 'auto', marginRight: 'auto' }}>
          <input hidden
            accept="application/json"
            style={{ display: 'none' }}
            id="raised-button-file"
            type="file"
            onChange={handleFileUpload}
          />
          <label htmlFor="raised-button-file">
            <Button component="span">
              Upload
            </Button>
          </label>
        </Box>
        <Divider />
        <FormGroup style={{ padding: 10 }}>
          <FormControlLabel control={<Checkbox checked={config?.include_all_nodes} />}
            label="Show all nodes" onChange={handleShowAllNodes} />
          <Divider />
          
        </FormGroup>
        <TextField label="Search" onChange={e => setSearchString(e.target.value)} />
      </Drawer>
      <Main open={open}>
        <DrawerHeader />
        <Container sx={{ display: 'flex', width: '100%', height: '100%', justifyContent: 'center' }}>
          
        </Container>
      </Main>
    </Box>
  );
}


export default ConfigurationPanel;
