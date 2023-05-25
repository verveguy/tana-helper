/*
  This is a React based app which is the Configuration page
  for tana-helper

  Right now, it lets you configure schemas for webhooks
  
*/

import React, { useEffect, useState } from "react";
import { FormControlLabel, FormGroup, Switch, TextField } from "@mui/material";

import { initial_config } from "./Extensions";

const ConfigurationPanel = () => {
  const [configuration, setConfiguration] = useState(initial_config);
  const [savedState, setSavedState] = useState("Initial");
  const [shouldLoadConfig, setShouldLoadConfig] = useState(true);

  const saveConfiguration = (configkey: string, propertykey: string, newValue: any) => {
    configuration[configkey].properties[propertykey].value = newValue;
    // update local react state
    setConfiguration(configuration);
    setSavedState("saving");
    chrome.storage.sync.set({ configuration }).then(() => { setSavedState("saved"); });
  }

  const handleToggle = (configkey: string, propertykey: string,) => {
    let currentValue: boolean = configuration[configkey].properties[propertykey].value;
    saveConfiguration(configkey, propertykey, !currentValue);
  }

  useEffect(() => {
    chrome.storage.sync.get("configuration").then((data) => {
      Object.assign(configuration, data.configuration);
      setConfiguration(configuration);
      setShouldLoadConfig(false);
    });
  }, [shouldLoadConfig]);

  // super simple React UI at this point
  let count = 0;
  return (
    <div id="tana-helper">
      <FormGroup>
        {Object.entries(configuration).map(([configkey, config]) => {
          count++;
          return (
            <div>
              <h2>{config.label}</h2>
              {Object.entries(config.properties).map(([propertykey, property]) => {
                if (property.type == "string") {
                  return (
                    <div>
                      <TextField style={{ width: '100%' }}
                        autoFocus={count != 1}
                        value={property.value}
                        onChange={e => saveConfiguration(configkey, propertykey, e.target.value)}
                        variant="outlined"
                        label={property.label}
                      />
                      <div style={{ height: '12px' }} />
                    </div>
                  )
                }
                else if (property.type == "boolean") {
                  return (
                    <div>
                      <FormControlLabel style={{ width: '100%' }}
                        control={
                          <Switch
                            checked={property.value == true}
                            onChange={e => handleToggle(configkey, propertykey)}
                          />}
                        label={property.label}
                      />
                      <div style={{ height: '12px' }} />
                    </div>
                  )
                }
              })}
            </div>
          )
        })}
      </FormGroup>
    </div>
  );
}


export default ConfigurationPanel;
