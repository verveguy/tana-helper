import React, { useContext, useEffect, useState } from "react";
import { Button, CardContent, FormControl, InputLabel, OutlinedInput, TextField } from "@mui/material";

// Replace context with Zustand store
import { useConfig, useConfigActions } from "../hooks/useAppStore";

export default function Configure() {
  // Use Zustand hooks instead of context
  const config = useConfig();
  const { setConfig, loadConfig, saveConfig } = useConfigActions();
  
  const [localConfig, setLocalConfig] = useState(config || {});

  useEffect(() => {
    if (config) {
      setLocalConfig(config);
    } else {
      // Load config on mount if not available
      loadConfig().catch(console.error);
    }
  }, [config, loadConfig]);

  const handleSave = async () => {
    try {
      await saveConfig(localConfig);
      // Success feedback could be added here
    } catch (error) {
      console.error('Failed to save config:', error);
      // Error feedback could be added here
    }
  };

  const handleChange = (key: string, value: any) => {
    setLocalConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };

  return (
    <CardContent>
      <FormControl margin="normal" size="small" fullWidth>
        <InputLabel htmlFor="openai_api_key">OpenAI API Key</InputLabel>
        <OutlinedInput
          id="openai_api_key"
          value={localConfig.openai_api_key || ''}
          onChange={(e) => handleChange('openai_api_key', e.target.value)}
          label="OpenAI API Key"
          type="password"
        />
      </FormControl>
      
      <Button 
        variant="contained" 
        color="primary" 
        onClick={handleSave}
        sx={{ mt: 2 }}
      >
        Save Configuration
      </Button>
    </CardContent>
  );
}