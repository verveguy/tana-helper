import React, { useEffect, useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";

// Replace context with Zustand store
import { useConfig, useConfigActions } from "../hooks/useAppStore";

export default function Configure() {
  // Use Zustand hooks instead of context
  const config = useConfig();
  const { setConfig, loadConfig, saveConfig } = useConfigActions();
  
  const [localConfig, setLocalConfig] = useState(config || {});
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (config) {
      setLocalConfig(config);
    } else {
      // Load config on mount if not available
      loadConfig().catch(console.error);
    }
  }, [config, loadConfig]);

  const handleSave = async () => {
    setIsLoading(true);
    try {
      await saveConfig(localConfig);
      // Success feedback could be added here
    } catch (error) {
      console.error('Failed to save config:', error);
      // Error feedback could be added here
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (key: string, value: any) => {
    setLocalConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Configuration</CardTitle>
        <CardDescription>
          Configure your Tana Helper settings
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="openai_api_key" className="text-sm font-medium">
            OpenAI API Key
          </label>
          <Input
            id="openai_api_key"
            type="password"
            value={localConfig.openai_api_key || ''}
            onChange={(e) => handleChange('openai_api_key', e.target.value)}
            placeholder="Enter your OpenAI API key"
          />
        </div>
        
        <Button 
          onClick={handleSave}
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? 'Saving...' : 'Save Configuration'}
        </Button>
      </CardContent>
    </Card>
  );
}