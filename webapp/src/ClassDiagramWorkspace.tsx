/*

  Visualize a Tana Workspace in #d

  Thanks to the amazing https://github.com/vasturiano/react-force-graph

*/


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
import ForceGraph2D, { GraphData } from 'react-force-graph-2d';
import { Button, Checkbox, CircularProgress, FormControlLabel, FormGroup, Grid, TextField } from '@mui/material';
import axios from 'axios';
import { Container } from "@mui/system";
import { useWindowSize } from "@react-hook/window-size";
import { Id, Index } from "flexsearch-ts";

const drawerWidth = 240;

// link types from our backend
// See service/service/tanaparser.py

const IS_INLINE_REF_LINK='iin'
const IS_INDIRECT_REF_LINK='iir'
const IS_TAG_LINK='itl'
const IS_TAG_TAG_LINK='itn'
const IS_CHILD_CONTENT_LINK='icl'

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


export default function ClassDiagramWorkspace() {
  const theme = useTheme();
  const [open, setOpen] = useState(true);
  const [rawGraphData, setRawGraphData] = useState<GraphData>();
  const [graphData, setGraphData] = useState<GraphData>();
  const [dumpFile, setDumpFile] = useState<File>();
  const [upload, setUpload] = useState(false);
  const [searchString, setSearchString] = useState('');
  const [loading, setLoading] = useState(false);
  const [index, setIndex] = useState(new Index({}));
  const [width, height] = useWindowSize();
  const fgRef = useRef();

  const handleDrawerOpen = () => {
    setOpen(true);
  };

  const handleDrawerClose = () => {
    setOpen(false);
  };

  const handleFileUpload = (event: React.FormEvent<HTMLInputElement>) => {
    const target = event.currentTarget;
    const file = target.files?.[0];
    setDumpFile(file);
    setUpload(true);
    event.currentTarget.files = null;
  };

  useEffect(() => {
    if (upload) {
      setLoading(true);
      axios.post('/class_diagram', dumpFile, {
        headers: {
          "Content-Type": "application/json",
        }
      })
        .then(response => {
          let new_graph = response.data as GraphData;
          setRawGraphData(new_graph);
          // buld new search index
          if (new_graph) {

            const index = new Index({preset: "match"})
            new_graph.nodes.forEach((node) => {
              index.add(node.id as Id, node.name)
            })

            setIndex(index);
          }
        })
        .catch(error => {
          console.error(error);
        })
        .finally(() => {
          setLoading(false);
          setUpload(false);
        })
    }
  }, [upload]);

  function get_id_from(obj: any): string {
    let id: string = obj as string;
    if (id && typeof id != 'string') {
      id = obj['id'];
    }
    return id;
  }

  useEffect(() => {
    // filter the response based on flag settings
    if (rawGraphData) {
      // first copy the raw data so we start with full set
      let new_graph = { ...rawGraphData };

      // build a search result set based on searchString
      let search_dict;
      let new_search_dict = {};
      if (searchString && searchString != '') {
        const search = index.search(searchString);
        // convert search to hash
        search_dict = search.reduce((search_dict, id_str) => {
          search_dict[id_str] = {};
          return search_dict;
        }, {});
        // and prepare a copy of the search results
        new_search_dict = { ...search_dict };
      }

      // filter links based on config and search index
      const new_links = rawGraphData.links.filter((link) => {
        // config is easy, check link types
        let found = true;
        // complex polymorphic stuff here since the graph engine seems to mutate
        // the link structure _sometimes_
        let source_id = get_id_from(link.source);
        let target_id = get_id_from(link.target);

        // search index is harder
        // should we search?
        if (search_dict != undefined) {
          found = false;
          // if the node at either end is included, include the whole link
          if (source_id in search_dict || target_id in search_dict) {
            found = true;
          }
        }

        // whether we searched or not, is this link found?
        if (found) {
          // ensure nodes at both end of links are included
          // by updating search index to include them
          if (!(source_id in new_search_dict)) {
            new_search_dict[source_id] = {}
          };
          if (!(target_id in new_search_dict)) {
            new_search_dict[target_id] = {}
          };
        }
        return found;
      });

      new_graph.links = new_links;

      // now filter nodes as well based on search index
      const new_nodes = new_graph.nodes.filter((node) => {
        let found = false;
        if (node.id && node.id in new_search_dict) {
          found = true;
        }
        return found;
      });

      new_graph.nodes = new_nodes;
      setGraphData(new_graph);
    }
  }, [rawGraphData, searchString]);


  // TODO: rework this to be cleaner React.
  // See example:
  // https://github.com/vasturiano/react-force-graph/blob/master/example/click-to-focus/index.html
  const handleNodeClick = useCallback(node => {
    // Aim at node from outside it
    const distance = 150;
    const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
    if (fgRef) {
      // @ts-ignore tricky type deref here
      fgRef.current?.cameraPosition(
        { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }, // new position
        node, // lookAt ({ x, y, z })
        3000  // ms transition duration
      );
    }
  }, [fgRef]);

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
            Tana Workspace Class Diagram
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
        <TextField label="Search" onChange={e => setSearchString(e.target.value)} />
      </Drawer>
      <Main open={open}>
        <DrawerHeader />
        <Container sx={{ display: 'flex', width: '100%', height: '100%', justifyContent: 'center', backgroundColor: 'white' }}>
          {loading
            ?
            <CircularProgress />
            // : <ForceGraph3D ref={fgRef}
            //   graphData={graphData}
            //   width={width - 50 - (open ? drawerWidth : 0)}
            //   height={height - 115}
            //   onNodeClick={handleNodeClick}
            //   onNodeDragEnd={node => {
            //     node.fx = node.x;
            //     node.fy = node.y;
            //     node.fz = node.z;
            //   }}
            : <ForceGraph2D graphData={graphData}
            width={width - 50 - (open ? drawerWidth : 0)}
            height={height - 115}
            onNodeClick={handleNodeClick}
            onNodeDragEnd={node => {
                node.fx = node.x;
                node.fy = node.y;
            }}
            />
          }
        </Container>
      </Main>
    </Box>
  );
}
