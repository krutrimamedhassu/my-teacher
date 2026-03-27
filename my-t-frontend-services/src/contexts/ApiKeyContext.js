import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getUserApiKeys } from '../services';

const ApiKeyContext = createContext();

export const useApiKey = () => {
  const context = useContext(ApiKeyContext);
  if (!context) {
    throw new Error('useApiKey must be used within an ApiKeyProvider');
  }
  return context;
};

export const ApiKeyProvider = ({ children }) => {
  const [apiKeys, setApiKeys] = useState([]);
  const [selectedApiKey, setSelectedApiKey] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadApiKeys = useCallback(async () => {
    setLoading(true);
    try {
      const keys = await getUserApiKeys();
      setApiKeys(keys);
      
      // Auto-select the first active API key if none is selected
      if (!selectedApiKey && keys.length > 0) {
        const activeKey = keys.find(key => key.is_active);
        if (activeKey) {
          setSelectedApiKey(activeKey.api_key);
        }
      }
    } catch (error) {
      console.error('Error loading API keys:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedApiKey]);

  // Load API keys when context is initialized
  useEffect(() => {
    loadApiKeys();
  }, [loadApiKeys]);

  const selectApiKey = (apiKey) => {
    setSelectedApiKey(apiKey);
  };

  const clearSelectedApiKey = () => {
    setSelectedApiKey(null);
  };

  const refreshApiKeys = () => {
    loadApiKeys();
  };

  const value = {
    apiKeys,
    selectedApiKey,
    loading,
    selectApiKey,
    clearSelectedApiKey,
    refreshApiKeys
  };

  return (
    <ApiKeyContext.Provider value={value}>
      {children}
    </ApiKeyContext.Provider>
  );
};

