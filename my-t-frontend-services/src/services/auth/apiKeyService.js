/**
 * API Key Management service
 * Contains all API key-related API functions
 */

import { apiRequest } from '../../utils/apiRequest';

// Create a new API key
export const createApiKey = async (name, description) => {
  const data = {
    name,
    description
  };

  return apiRequest('/api-keys/create', 'POST', data);
};

// Get all API keys for the current user
export const getUserApiKeys = async () => {
  return apiRequest('/api-keys/', 'GET');
};

// Update an existing API key
export const updateApiKey = async (keyId, updateData) => {
  const data = {
    name: updateData.name,
    description: updateData.description,
    is_active: updateData.isActive
  };

  return apiRequest(`/api-keys/${keyId}`, 'PUT', data);
};

// Delete an API key
export const deleteApiKey = async (keyId) => {
  return apiRequest(`/api-keys/${keyId}`, 'DELETE');
};

// Get usage statistics for API keys
export const getApiKeyUsage = async () => {
  return apiRequest('/api-keys/usage', 'GET');
};

// Get current user's tier information
export const getTierInformation = async () => {
  // Backend endpoint: GET /api/v1/auth/tier
  return apiRequest('/auth/tier', 'GET');
};

