import { useEffect, useState } from 'react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';

// Replace context with Zustand store
import { useConfig, useConfigActions, useConfigLoading } from '../hooks/useAppStore';

export default function Configure() {
  // Use Zustand hooks instead of context
  const config = useConfig();
  const configLoading = useConfigLoading();
  const { loadConfig, saveConfig } = useConfigActions();

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
      [key]: value,
    }));
  };

  return (
    <div className="w-full max-w-2xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Configuration</h1>
        <p className="text-muted-foreground">Configure your Tana Helper settings</p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="openai_api_key" className="text-sm font-medium">
            OpenAI API Key
          </label>
          <Input
            id="openai_api_key"
            type="password"
            value={localConfig.openai_api_key || ''}
            onChange={e => handleChange('openai_api_key', e.target.value)}
            placeholder="Enter your OpenAI API key"
          />
        </div>

        <Button onClick={handleSave} disabled={configLoading} className="w-full">
          {configLoading ? 'Saving...' : 'Save Configuration'}
        </Button>
      </div>
    </div>
  );
}
