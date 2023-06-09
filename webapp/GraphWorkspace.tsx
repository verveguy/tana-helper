import React, { SyntheticEvent, useEffect, useState } from "react";
import { styled, useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import CssBaseline from '@mui/material/CssBaseline';
import MuiAppBar, { AppBarProps as MuiAppBarProps } from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import List from '@mui/material/List';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import InboxIcon from '@mui/icons-material/MoveToInbox';
import MailIcon from '@mui/icons-material/Mail';
import ForceGraph3D, { GraphData } from 'react-force-graph-3d';
import { Button, Checkbox, CircularProgress, FormControlLabel, FormGroup } from '@mui/material';
import axios from 'axios';

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

type GraphConfig = {
  include_tag_nodes: boolean;
  include_inline_refs: boolean;
  include_inline_ref_nodes: boolean;
}

export default function GraphWorkspace() {
  const theme = useTheme();
  const [open, setOpen] = useState(true);
  const [graphData, setGraphData] = useState<GraphData>();
  const [config, setConfig] = useState<GraphConfig>();
  const [file, setFile] = useState<File>();
  const [upload, setUpload] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleDrawerOpen = () => {
    setOpen(true);
  };

  const handleDrawerClose = () => {
    setOpen(false);
  };

  const handleFileUpload = (event: React.FormEvent<HTMLInputElement>) => {
    const target = event.currentTarget;
    const file = target.files?.[0];
    console.log(file);
    setFile(file);
    setUpload(true);
    event.currentTarget.files = null;
  };

  useEffect(() => {
    setLoading(true);
    axios.post('/graph', file, {
      headers: {
        "Content-Type": "application/json",
      }
    })
      .then(response => {
        setGraphData(response.data);
      })
      .catch(error => {
        console.error(error);
      })
      .finally(() => {
        setLoading(false);
        setUpload(false)
      })
  }, [upload]);

  useEffect(() => {
    axios.post('/graph/config', config, {
      headers: {
        "Content-Type": "application/json",
      }
    })
      .then(response => {
        console.log(response);
      })
      .catch(error => {
        console.error(error);
      });
  }, [config]);

  function handleIncludeTags(event: SyntheticEvent<Element, Event>, checked: boolean): void {
    let new_config = { ...config } as GraphConfig;
    new_config.include_tag_nodes = checked;
    setConfig(new_config);
    setUpload(true);
  }

  function handleIncludeRefs(event: SyntheticEvent<Element, Event>, checked: boolean): void {
    let new_config = { ...config } as GraphConfig;
    new_config.include_inline_refs = checked;
    // turn off inline ref nodes since we can't have it on if we are off
    if (!checked) {
      new_config.include_inline_ref_nodes = false;
    }
    setConfig(new_config);
    setUpload(true);
  }

  function handleIncludeRefNodes(event: SyntheticEvent<Element, Event>, checked: boolean): void {
    let new_config = { ...config } as GraphConfig;
    new_config.include_inline_ref_nodes = checked;
    setConfig(new_config);
    setUpload(true);
  }

  return (
    <Box sx={{ display: 'flex' }}>
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
            Tana Workspace Visualizer
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
        <Box style={{ padding:10, marginLeft: 'auto', marginRight: 'auto'}}>
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
        <FormGroup style={{ padding:10}}>
          <FormControlLabel control={<Checkbox checked={config?.include_tag_nodes} />} label="Include Tags as Nodes" onChange={handleIncludeTags} />
          <FormControlLabel control={<Checkbox checked={config?.include_inline_refs}/>} label="Include inline refs as joins" onChange={handleIncludeRefs} />
          <FormControlLabel control={<Checkbox checked={config?.include_inline_ref_nodes}/>} disabled={!config?.include_inline_refs} label="Include inline refs joins as nodes" onChange={handleIncludeRefNodes} />
        </FormGroup>
      </Drawer>
      <Main open={open}>
        <DrawerHeader />
        { loading ? <CircularProgress />
        : <ForceGraph3D graphData={graphData}
          onNodeDragEnd={node => {
            node.fx = node.x;
            node.fy = node.y;
            node.fz = node.z;
          }}
        />
        }
      </Main>
    </Box>
  );
}
