/*
  This is a React based app which is the Configuration page
  for tana-helper

  Right now, it lets you configure schemas for webhooks
  
*/

import React, { useEffect, useState } from "react";
import { FormControlLabel, FormGroup, Switch, TextField } from "@mui/material";
import axios from 'axios';

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
export default ConfigurationPanel;
