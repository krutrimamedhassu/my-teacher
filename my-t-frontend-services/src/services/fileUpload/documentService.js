/**
 * Document upload and management service
 * Contains all file upload and document-related API functions
 */

import { apiRequest } from '../../utils/apiRequest';

// Upload API
export const uploadDocument = async (file, conversationId) => {
  const formData = new FormData();
  formData.append('file', file);

  // Build URL with conversation_id as query parameter
  let endpoint = '/upload/';
  if (conversationId) {
    endpoint += `?conversation_id=${encodeURIComponent(conversationId)}`;
  }

  try {
    console.log('📤 uploadDocument: Uploading file:', file.name, 'to conversation:', conversationId);
    console.log('📤 uploadDocument: Using endpoint:', endpoint);
    console.log('📤 uploadDocument: Conversation ID is:', conversationId, 'Type:', typeof conversationId);
    const response = await apiRequest(endpoint, 'POST', formData, true);
    console.log('📤 uploadDocument: Success response:', response);
    return response;
  } catch (error) {
    console.error('📤 uploadDocument: Error uploading file:', file.name, 'Error:', error);
    throw error;
  }
};

/**
 * Upload multiple documents in a single request.
 * Backend expects FormData with repeated 'file' fields and conversation_id as query parameter.
 * Uses the /upload/upload-multiple endpoint (proxied to /api/v1 in dev).
 * @param {File[]} files
 * @param {string} conversationId
 * @returns {Promise<any>} backend response containing uploaded document metadata
 */
export const uploadMultipleDocuments = async (files, conversationId) => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  // Build URL with conversation_id as query parameter
  let endpoint = '/upload/upload-multiple';
  if (conversationId) {
    endpoint += `?conversation_id=${encodeURIComponent(conversationId)}`;
  }

  try {
    console.log('📤 uploadMultipleDocuments: Uploading', files.length, 'files to conversation:', conversationId);
    console.log('📤 uploadMultipleDocuments: Using endpoint:', endpoint);
    const response = await apiRequest(endpoint, 'POST', formData, true);
    console.log('📤 uploadMultipleDocuments: Success response:', response);
    return response;
  } catch (error) {
    console.error('📤 uploadMultipleDocuments: Error uploading files, Error:', error);
    throw error;
  }
};

export const listDocuments = async (limit = 50) => {
  const queryParams = new URLSearchParams({ limit }).toString();
  return apiRequest(`/docs?${queryParams}`, 'GET');
};

export const getDocument = async (documentId) => {
  return apiRequest(`/docs/${documentId}`, 'GET');
};

export const deleteDocument = async (documentId) => {
  return apiRequest(`/docs/${documentId}`, 'DELETE');
};

export const getDocumentContent = async (documentId) => {
  return apiRequest(`/docs/${documentId}/content`, 'GET');
};

export const getSupportedTypes = async () => {
  return apiRequest('/upload/limits', 'GET');
};