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
// import ForceGraph2D, { GraphData } from 'react-force-graph-2d';
import { Button, Checkbox, CircularProgress, FormControlLabel, FormGroup, Grid, TextField } from '@mui/material';
import axios from 'axios';
import { Container } from "@mui/system";
import Grid2 from "@mui/material/Unstable_Grid2/Grid2";
import { useWindowSize } from "@react-hook/window-size";
import { Id, Index } from "flexsearch-ts";
import FlexSearch from "flexsearch";

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

interface GraphConfig {
  include_all_nodes: boolean;
  include_tag_nodes: boolean;
  include_tag_links: boolean;
  include_inline_refs: boolean;
  include_inline_ref_nodes: boolean;
}

export default function GraphWorkspace() {
  const theme = useTheme();
  const [open, setOpen] = useState(true);
  const [rawGraphData, setRawGraphData] = useState<GraphData>();
  const [graphData, setGraphData] = useState<GraphData>();
  const [config, setConfig] = useState<GraphConfig>();
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
    let new_config: GraphConfig = { include_all_nodes: true, include_tag_nodes: false, include_tag_links: false, include_inline_ref_nodes: false, include_inline_refs: false };
    setConfig(new_config)
  }, []);

  useEffect(() => {
    if (upload) {
      setLoading(true);
      axios.post('/graph', dumpFile, {
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
        let found = (link.reason == 'iin' && config?.include_inline_ref_nodes)
          || (link.reason == 'iir' && config?.include_inline_refs)
          || (link.reason == 'itl' && config?.include_tag_links)
          || (link.reason == 'itn' && config?.include_tag_nodes);

        // complex polymorphic stuff here since the graph engine seems to mutate
        // the link structure _sometimes_
        let source_id = get_id_from(link.source);
        let target_id = get_id_from(link.target);

        // search index is harder
        if (found) {
          // should we search?
          if (search_dict != undefined) {
            found = false;
            // if the node at either end is included, include the whole link
            if (source_id in search_dict || target_id in search_dict) {
              found = true;
            }
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
        let found = (config?.include_all_nodes == true);
        if (node.id && node.id in new_search_dict) {
          found = true;
        }
        return found;
      });

      new_graph.nodes = new_nodes;
      setGraphData(new_graph);
    }
  }, [config, rawGraphData, searchString]);


  function handleShowAllNodes(event: SyntheticEvent<Element, Event>, checked: boolean): void {
    let new_config = { ...config } as GraphConfig;
    new_config.include_all_nodes = checked;
    setConfig(new_config);
  }

  function handleShowTagTagLinks(event: SyntheticEvent<Element, Event>, checked: boolean): void {
    let new_config = { ...config } as GraphConfig;
    new_config.include_tag_nodes = checked;
    setConfig(new_config);
  }


  function handleIncludeTagLinks(event: SyntheticEvent<Element, Event>, checked: boolean): void {
    let new_config = { ...config } as GraphConfig;
    new_config.include_tag_links = checked;
    setConfig(new_config);
  }

  function handleShowInlineRefs(event: SyntheticEvent<Element, Event>, checked: boolean): void {
    let new_config = { ...config } as GraphConfig;
    new_config.include_inline_refs = checked;
    setConfig(new_config);
  }

  function handleIncludeInlineNodes(event: SyntheticEvent<Element, Event>, checked: boolean): void {
    let new_config = { ...config } as GraphConfig;
    new_config.include_inline_ref_nodes = checked;
    setConfig(new_config);
  }

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
          <FormControlLabel control={<Checkbox checked={config?.include_tag_nodes} />}
            label="Show supertag 'extends' as links" onChange={handleShowTagTagLinks} />
          <Divider />
          <FormControlLabel control={<Checkbox checked={config?.include_tag_links} />}
            label="Show node tags as links" onChange={handleIncludeTagLinks} />
          <Divider />
          <FormControlLabel control={<Checkbox checked={config?.include_inline_refs} />}
            label="Show inline refs as links" onChange={handleShowInlineRefs} />
          <Divider />
          <FormControlLabel control={<Checkbox checked={config?.include_inline_ref_nodes} />}
            label="Show inline ref node links" onChange={handleIncludeInlineNodes} />
          <FormControlLabel control={<Checkbox disabled={true} />}
            label="Show fields as links" />
          <FormControlLabel control={<Checkbox disabled={true} />}
            label="Show child links" />
          <Divider />
        </FormGroup>
        <TextField label="Search" onChange={e => setSearchString(e.target.value)} />
      </Drawer>
      <Main open={open}>
        <DrawerHeader />
        <Container sx={{ display: 'flex', width: '100%', height: '100%', justifyContent: 'center' }}>
          {loading
            ?
            <CircularProgress />
            : <ForceGraph3D ref={fgRef}
              graphData={graphData}
              width={width - 50 - (open ? drawerWidth : 0)}
              height={height - 115}
              onNodeClick={handleNodeClick}
              onNodeDragEnd={node => {
                node.fx = node.x;
                node.fy = node.y;
                node.fz = node.z;
              }}
            // : <ForceGraph2D graphData={graphData}
            //   onNodeDragEnd={node => {
            //     node.fx = node.x;
            //     node.fy = node.y;
            // }}
            />
          }
        </Container>
      </Main>
    </Box>
  );
}
