/**
 * Conversation service
 * Contains all conversation-related API functions
 */

import { apiRequest } from '../../utils/apiRequest';

// Conversations API
export const createConversation = async ({ conversation_id, user_id, username, title } = {}) => {
  const data = {};
  if (conversation_id) data.conversation_id = conversation_id;
  if (user_id) data.user_id = user_id;
  if (username) data.username = username;
  if (title) data.title = title;
  return apiRequest('/conversations/create_id', 'POST', data);
};

// List all conversations for a user (by user_id)
export const listConversations = async ({ user_id }) => {
  if (!user_id) throw new Error('user_id is required');
  return apiRequest(`/conversations/user/${encodeURIComponent(user_id)}`, 'GET');
};

// Get a conversation and its messages by conversation_id
export const getConversationById = async (conversation_id) => {
  if (!conversation_id) throw new Error('conversation_id is required');
  return apiRequest(`/conversations/${encodeURIComponent(conversation_id)}`, 'GET');
};

// Send a message to a conversation
export const sendMessageToConversation = async (conversation_id, message) => {
  if (!conversation_id) throw new Error('conversation_id is required');
  return apiRequest(`/conversations/${encodeURIComponent(conversation_id)}/messages`, 'POST', message);
};

// Edit a conversation (PATCH)
export const editConversation = async (conversation_id, data) => {
  if (!conversation_id) throw new Error('conversation_id is required');
  return apiRequest(`/conversations/${encodeURIComponent(conversation_id)}`, 'PATCH', data);
};

// Delete a conversation (DELETE)
export const deleteConversation = async (conversation_id) => {
  if (!conversation_id) throw new Error('conversation_id is required');
  return apiRequest(`/conversations/${encodeURIComponent(conversation_id)}`, 'DELETE');
};

// Get sidebar_info for a conversation
export const getConversationSidebarInfo = async (conversation_id) => {
  if (!conversation_id) throw new Error('conversation_id is required');
  return apiRequest(`/conversations/${encodeURIComponent(conversation_id)}/sidebar_info`, 'GET');
};

// Delete all empty conversations for the current authenticated user
export const deleteEmptyConversations = async () => {
  return apiRequest('/conversations/empty', 'DELETE');
};

// Get documents for a conversation
export const getConversationDocuments = async (conversation_id) => {
  if (!conversation_id) throw new Error('conversation_id is required');
  return apiRequest(`/conversations/${encodeURIComponent(conversation_id)}/documents`, 'GET');
};

// Delete a document from a conversation
export const deleteConversationDocument = async (conversation_id, document_id, delete_references = true) => {
  if (!conversation_id) throw new Error('conversation_id is required');
  if (!document_id) throw new Error('document_id is required');
  
  const queryParams = new URLSearchParams();
  if (delete_references) {
    queryParams.append('delete_references', 'true');
  }
  
  const url = `/conversations/${encodeURIComponent(conversation_id)}/documents/${encodeURIComponent(document_id)}?${queryParams}`;
  return apiRequest(url, 'DELETE');
};