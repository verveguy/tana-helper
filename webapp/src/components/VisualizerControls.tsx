import React, { SyntheticEvent, useContext, useEffect, useState } from "react";
import { Box, Button, Checkbox, Divider, FormControlLabel, FormGroup, TextField } from "@mui/material";

import { GraphData } from 'react-force-graph-3d';
// import ForceGraph2D, { GraphData } from 'react-force-graph-2d';
import axios from 'axios';
import { Id, Index } from "flexsearch-ts";
import { TanaHelperContext } from "../TanaHelperContext";

interface GraphConfig {
  include_all_nodes: boolean;
  include_tag_nodes: boolean;
  include_tag_links: boolean;
  include_inline_refs: boolean;
  include_inline_ref_nodes: boolean;
}


// link types from our backend
// See service/service/tanaparser.py

const IS_INLINE_REF_LINK = 'iin'
const IS_INDIRECT_REF_LINK = 'iir'
const IS_TAG_LINK = 'itl'
const IS_TAG_TAG_LINK = 'itn'
const IS_CHILD_CONTENT_LINK = 'icl'


export default function VisualizerControls() {
  const { graphData, setGraphData, loading, setLoading, twoDee, setTwoDee } = useContext(TanaHelperContext)
  const [open, setOpen] = useState(true);
  const [rawGraphData, setRawGraphData] = useState<GraphData>();
  const [config, setConfig] = useState<GraphConfig>({ include_all_nodes: true, include_tag_nodes: false, include_tag_links: false, include_inline_ref_nodes: false, include_inline_refs: false });
  const [dumpFile, setDumpFile] = useState<File>();
  const [upload, setUpload] = useState(false);
  const [searchString, setSearchString] = useState('');
  const [index, setIndex] = useState(new Index({}));

  const handleFileUpload = (event: React.FormEvent<HTMLInputElement>) => {
    const target = event.currentTarget;
    const file = target.files?.[0];
    setDumpFile(file);
    setUpload(true);
    // reset input field so we can upload another file later
    event.currentTarget.value = "";
  };

  // useEffect(() => {
  //   let new_config: GraphConfig = { include_all_nodes: true, include_tag_nodes: false, include_tag_links: false, include_inline_ref_nodes: false, include_inline_refs: false };
  //   setConfig(new_config)
  // }, []);

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

            const index = new Index({ preset: "match" })
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
        let found = (link.reason == IS_INLINE_REF_LINK && config?.include_inline_ref_nodes)
          || (link.reason == IS_INDIRECT_REF_LINK && config?.include_inline_refs)
          || (link.reason == IS_TAG_LINK && config?.include_tag_links)
          || (link.reason == IS_TAG_TAG_LINK && config?.include_tag_nodes);

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


  function handleTwoDee(event: SyntheticEvent<Element, Event>, checked: boolean): void {
    setTwoDee(checked);
  }

  return (
    <div>
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
          <Button component="span" sx={{ width: '100%', alignContent: 'center' }}>
            <span style={{ fontSize: 14 }}>
              Upload
            </span>
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
        <FormControlLabel control={<Checkbox checked={twoDee} />}
          label="2D" onChange={handleTwoDee} />
        <Divider />
      </FormGroup>
      <TextField label="Search" onChange={e => setSearchString(e.target.value)} />
    </div>
  );

}
