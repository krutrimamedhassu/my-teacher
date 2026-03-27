/**
 * Helper functions to test token expiration and refresh functionality
 * Use these in browser console to test the implementation
 */

import { TokenManager } from './apiRequest';

// Test function to simulate an expired token
export const simulateExpiredToken = () => {
  const accessToken = TokenManager.getAccessToken();
  if (!accessToken) {
    console.log('No access token found');
    return;
  }

  try {
    // Decode the current token
    const payload = JSON.parse(atob(accessToken.split('.')[1]));
    
    // Create a new token with expired timestamp (1 hour ago)
    const expiredPayload = {
      ...payload,
      exp: Math.floor(Date.now() / 1000) - 3600 // Expired 1 hour ago
    };
    
    // Create a fake expired token (this won't work with real backend validation)
    const header = JSON.parse(atob(accessToken.split('.')[0]));
    const fakeExpiredToken = 
      btoa(JSON.stringify(header)) + '.' + 
      btoa(JSON.stringify(expiredPayload)) + '.' + 
      accessToken.split('.')[2]; // Keep original signature
    
    localStorage.setItem('accessToken', fakeExpiredToken);
    console.log('✅ Access token set to expired state for testing');
    console.log('🔍 Use TokenManager.isAccessTokenExpired() to check');
    console.log('🔄 Make any API call to trigger automatic refresh');
    
  } catch (error) {
    console.error('Failed to simulate expired token:', error);
  }
};

// Test function to check token expiration
export const checkTokenExpiration = () => {
  const token = TokenManager.getAccessToken();
  if (!token) {
    console.log('❌ No access token found');
    return;
  }
  
  console.log('🔍 Token expiration check:');
  console.log('- Has token:', !!token);
  console.log('- Is expired:', TokenManager.isAccessTokenExpired());
  console.log('- Is authenticated:', TokenManager.isAuthenticated());
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Math.floor(Date.now() / 1000);
    const timeUntilExpiry = payload.exp - currentTime;
    
    console.log('- Expires at:', new Date(payload.exp * 1000));
    console.log('- Time until expiry:', Math.floor(timeUntilExpiry / 60), 'minutes');
    
    if (timeUntilExpiry < 600) {
      console.log('⚠️ Token expires in less than 10 minutes');
    }
  } catch (error) {
    console.error('Failed to decode token:', error);
  }
};

// Test function to manually trigger token refresh
export const testTokenRefresh = async () => {
  console.log('🔄 Testing manual token refresh...');
  try {
    await TokenManager.refreshAccessToken();
    console.log('✅ Token refreshed successfully');
    console.log('🔍 New token info:');
    checkTokenExpiration();
  } catch (error) {
    console.error('❌ Token refresh failed:', error);
  }
};

// Test function to clear all tokens
export const clearTokensForTesting = () => {
  TokenManager.clearTokens();
  console.log('🧹 All tokens cleared');
};

// Export functions for browser console testing
if (typeof window !== 'undefined') {
  window.tokenTestHelper = {
    simulateExpiredToken,
    checkTokenExpiration,
    testTokenRefresh,
    clearTokensForTesting,
    TokenManager
  };
  
  console.log('🧪 Token test helper loaded. Use window.tokenTestHelper in console to test:');
  console.log('- window.tokenTestHelper.checkTokenExpiration()');
  console.log('- window.tokenTestHelper.simulateExpiredToken()');
  console.log('- window.tokenTestHelper.testTokenRefresh()');
  console.log('- window.tokenTestHelper.clearTokensForTesting()');
}