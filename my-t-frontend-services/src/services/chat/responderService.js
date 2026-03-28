/**
 * AI Responder service
 * Contains AI chat and responder-related API functions
 */

import { apiRequest } from '../../utils/apiRequest';

// Chat/AI Responder API
export const analyzeUserInput = async (userInput, context = {}) => {
  const data = {
    user_input: userInput,
    context
  };

  return apiRequest('/responder/analyze', 'POST', data);
};

// Execute suggested request based on analysis
export const executeSuggestedRequest = async (suggestedRequest) => {
  const { endpoint, method, body } = suggestedRequest;
  
  // Remove the base URL from the endpoint if it's included
  const cleanEndpoint = endpoint.startsWith('/api/v1') 
    ? endpoint.replace('/api/v1', '') 
    : endpoint;
  
  return apiRequest(cleanEndpoint, method, body);
};

// Call the /responder/ endpoint directly
export const callResponderAPI = async (input, conversation_id, apiKey = null) => {
  const data = { input };
  if (conversation_id) data.conversation_id = conversation_id;
  
  // If API key is provided, use it for authentication instead of Bearer token
  if (apiKey) {
    const API_BASE = process.env.NODE_ENV === 'production'
      ? (process.env.REACT_APP_API_BASE_URL || '/api/v1')
      : '/api/v1';
    const url = `${API_BASE}/responder/`;
    
    const headers = {
      'Content-Type': 'application/json',
      'accept': 'application/json',
      'X-API-Key': apiKey
    };

    const options = {
      method: 'POST',
      headers,
      body: JSON.stringify(data)
    };

    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        // Check for limit exceeded error (common status codes: 429, 403, or 402)
        if (response.status === 429 || response.status === 403 || response.status === 402) {
          const errorData = await response.json().catch(() => ({}));
          const isLimitError = errorData.message && (
            errorData.message.toLowerCase().includes('limit') ||
            errorData.message.toLowerCase().includes('quota') ||
            errorData.message.toLowerCase().includes('exceeded')
          );
          
          if (isLimitError) {
            const limitError = new Error('You have reached your limit. Please upgrade to premium for unlimited access.');
            limitError.isLimitError = true;
            limitError.status = response.status;
            throw limitError;
          }
        }
        throw new Error(`API request failed with status ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('API request error:', error);
      throw error;
    }
  }
  
  // Fallback to regular Bearer token authentication
  return apiRequest('/responder/', 'POST', data);
};