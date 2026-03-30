/**
 * Authentication and user account services
 */

import { apiRequest, TokenManager } from '../../utils/apiRequest';

// Login user
export const loginUser = async (email, password) => {
  const data = await apiRequest('/auth/login', 'POST', { email, password });

  // Persist tokens if returned
  if (data?.access_token || data?.refresh_token) {
    TokenManager.setTokens(data.access_token, data.refresh_token);
  }

  // Persist user object for quick access elsewhere
  if (data?.user) {
    try {
      localStorage.setItem('user', JSON.stringify(data.user));
    } catch (_) {}
  }

  return data;
};

// Register user
export const registerUser = async ({ fullName, username, email, password }) => {
  const payload = {
    full_name: fullName,
    username,
    email,
    password
  };

  const data = await apiRequest('/auth/register', 'POST', payload);

  if (data?.access_token || data?.refresh_token) {
    TokenManager.setTokens(data.access_token, data.refresh_token);
  }
  if (data?.user) {
    try {
      localStorage.setItem('user', JSON.stringify(data.user));
    } catch (_) {}
  }
  return data;
};

// Get current authenticated user
export const getCurrentUser = async () => {
  return apiRequest('/auth/me', 'GET');
};

// Enhanced auth check - verifies token existence and expiration
export const checkAuthentication = async () => {
  const token = TokenManager.getAccessToken();
  
  // No token = not authenticated
  if (!token) return false;
  
  // Check if token is expired
  if (TokenManager.isAccessTokenExpired()) {
    console.log('🔐 checkAuthentication: Access token expired, checking refresh token');
    
    // Try to refresh if we have a refresh token
    if (TokenManager.getRefreshToken()) {
      try {
        await TokenManager.refreshAccessToken();
        return true; // Successfully refreshed
      } catch (error) {
        console.log('🔐 checkAuthentication: Refresh failed, user needs to login again');
        TokenManager.clearTokens();
        return false;
      }
    } else {
      console.log('🔐 checkAuthentication: No refresh token, user needs to login again');
      TokenManager.clearTokens();
      return false;
    }
  }
  
  return true; // Token exists and is not expired
};

// Logout user (server + local cleanup)
export const logout = async () => {
  try {
    // Best-effort server logout if available
    await apiRequest('/auth/logout', 'POST').catch(() => {});
  } finally {
    TokenManager.clearTokens();
    try { localStorage.removeItem('user'); } catch (_) {}
  }
};

// Update password for current user
export const updatePassword = async (currentPassword, newPassword) => {
  const payload = { current_password: currentPassword, new_password: newPassword };
  return apiRequest('/auth/password', 'PUT', payload);
};

// Update email for current user
export const updateEmail = async (currentPassword, newEmail) => {
  const payload = { current_password: currentPassword, new_email: newEmail };
  return apiRequest('/auth/email', 'PUT', payload);
};

// User tier helpers (used in Settings)
export const getUserTier = async () => {
  // Backend exposes this under /auth/tier
  return apiRequest('/auth/tier', 'GET');
};

export const updateUserTier = async (tier) => {
  // Backend exposes this under /auth/tier
  return apiRequest('/auth/tier', 'PUT', { tier });
};

// Update basic profile fields
export const updateProfile = async (profileData) => {
  const payload = {
    full_name: profileData.fullName,
    username: profileData.username
  };
  return apiRequest('/auth/profile', 'PUT', payload);
};

// Upload profile picture
export const uploadProfilePicture = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return apiRequest('/auth/profile-image', 'POST', formData, true);
};

// Delete profile picture
export const deleteProfilePicture = async () => {
  const payload = { profile_image_url: "" };
  return apiRequest('/auth/profile', 'PUT', payload);
};


