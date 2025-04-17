import React, { useState, useEffect } from 'react';
import { useToast } from '@shopify/app-bridge-react';
import { PromptDashboard } from '../components/PromptDashboard';
import { useAPI } from '../hooks/useAPI';

export function PromptDashboardContainer({ storeId }) {
  const [promptData, setPromptData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [availableOptions, setAvailableOptions] = useState(null);
  const { show: showToast } = useToast();
  const api = useAPI();

  useEffect(() => {
    loadPromptData();
    loadAvailableOptions();
  }, [storeId]);

  const loadPromptData = async () => {
    try {
      const response = await api.get(`/api/stores/${storeId}/prompts/preferences`);
      setPromptData(response.data.prompt_preferences);
    } catch (error) {
      console.error('Failed to load prompt data:', error);
      showToast('Failed to load prompt settings', { isError: true });
    } finally {
      setIsLoading(false);
    }
  };

  const loadAvailableOptions = async () => {
    try {
      const response = await api.get('/api/prompts/options');
      setAvailableOptions(response.data);
    } catch (error) {
      console.error('Failed to load available options:', error);
      showToast('Failed to load prompt options', { isError: true });
    }
  };

  const handleSave = async (updatedData) => {
    try {
      setIsLoading(true);
      const response = await api.put(
        `/api/stores/${storeId}/prompts/preferences`,
        updatedData
      );
      
      if (response.data.prompt_preferences) {
        setPromptData(response.data.prompt_preferences);
        showToast('Prompt settings saved successfully');
      }
    } catch (error) {
      console.error('Failed to save prompt settings:', error);
      showToast('Failed to save prompt settings', { isError: true });
    } finally {
      setIsLoading(false);
    }
  };

  if (!promptData || !availableOptions) {
    return null; // or a loading spinner
  }

  return (
    <PromptDashboard
      promptData={promptData}
      onSave={handleSave}
      isLoading={isLoading}
      availableOptions={availableOptions}
    />
  );
} 