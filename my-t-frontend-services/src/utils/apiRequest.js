/**
 * API request helper and token manager
 */

const API_BASE_URL = process.env.REACT_APP_BASE_BACKEND_URL
  ? `${process.env.REACT_APP_BASE_BACKEND_URL}/api/v1`
  : (process.env.REACT_APP_API_BASE_URL || 'https://my-teacher-backend.vercel.app/api/v1');

export const TokenManager = {
  setTokens(accessToken, refreshToken) {
    if (accessToken) localStorage.setItem('accessToken', accessToken);
    if (refreshToken) localStorage.setItem('refreshToken', refreshToken);
  },
  getAccessToken() {
    return localStorage.getItem('accessToken');
  },
  getRefreshToken() {
    return localStorage.getItem('refreshToken');
  },
  clearTokens() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  },
  isAuthenticated() {
    return Boolean(localStorage.getItem('accessToken'));
  },
  
  // Decode JWT token to check expiration
  isTokenExpired(token) {
    if (!token) return true;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      return payload.exp < currentTime;
    } catch (error) {
      console.warn('Failed to decode token:', error);
      return true;
    }
  },
  
  // Check if access token is expired
  isAccessTokenExpired() {
    const token = this.getAccessToken();
    return this.isTokenExpired(token);
  },
  
  // Refresh access token using refresh token
  async refreshAccessToken() {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    
    console.log('🔄 TokenManager: Attempting to refresh access token');
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      
      if (!response.ok) {
        throw new Error(`Token refresh failed: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.access_token) {
        this.setTokens(data.access_token, data.refresh_token || refreshToken);
        console.log('✅ TokenManager: Access token refreshed successfully');
        return data.access_token;
      }
      
      throw new Error('No access token in refresh response');
    } catch (error) {
      console.error('❌ TokenManager: Token refresh failed:', error);
      this.clearTokens();
      throw error;
    }
  }
};

/**
 * Makes an API request to the backend with sensible defaults.
 * Automatically attaches Authorization header if an access token exists.
 *
 * @param {string} path - API path beginning with '/'
 * @param {string} method - HTTP method
 * @param {any} body - Request body (object or FormData)
 * @param {boolean} isFormData - When true, will not set JSON headers
 * @param {boolean} isRetry - When true, indicates this is a retry attempt after token refresh
 * @returns {Promise<any>} Parsed JSON response or throws Error
 */
export async function apiRequest(path, method = 'GET', body = undefined, isFormData = false, isRetry = false) {
  const urlPath = path.startsWith('/') ? path : `/${path}`;
  const url = `${API_BASE_URL}${urlPath}`;

  // Check if token is expired before making request (proactive refresh)
  if (TokenManager.isAuthenticated() && TokenManager.isAccessTokenExpired() && !isRetry) {
    try {
      console.log('🔄 apiRequest: Access token expired, refreshing proactively');
      await TokenManager.refreshAccessToken();
    } catch (error) {
      console.warn('⚠️ apiRequest: Proactive token refresh failed, will try reactive approach');
    }
  }

  const headers = {};
  const token = TokenManager.getAccessToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let fetchBody = undefined;
  if (body !== undefined && body !== null) {
    if (isFormData || body instanceof FormData) {
      fetchBody = body;
    } else {
      headers['Content-Type'] = 'application/json';
      fetchBody = JSON.stringify(body);
    }
  }

  console.log('🌐 apiRequest: Making request to:', url, 'method:', method);
  console.log('🌐 apiRequest: Full URL breakdown - API_BASE_URL:', API_BASE_URL, 'path:', path, 'urlPath:', urlPath);
  if (isFormData || body instanceof FormData) {
    console.log('🌐 apiRequest: Sending FormData with headers:', headers);
  }
  
  let response;
  try {
    response = await fetch(url, {
      method,
      headers,
      body: fetchBody,
    });
    console.log('🌐 apiRequest: Response received, status:', response.status);
  } catch (fetchError) {
    console.error('🌐 apiRequest: Fetch failed for URL:', url, 'Error:', fetchError);
    throw fetchError;
  }

  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');
  const data = isJson ? await response.json().catch(() => ({})) : await response.text();

  if (!response.ok) {
    const message = (isJson && (data?.message || data?.error)) || `HTTP error! status: ${response.status}`;
    
    // Handle 401 Unauthorized - try to refresh token and retry
    if (response.status === 401 && TokenManager.getRefreshToken() && !isRetry && !path.includes('/auth/refresh')) {
      try {
        console.log('🔄 apiRequest: Got 401, attempting token refresh and retry');
        await TokenManager.refreshAccessToken();
        
        // Retry the original request with new token
        return await apiRequest(path, method, body, isFormData, true);
      } catch (refreshError) {
        console.error('❌ apiRequest: Token refresh failed on 401, user needs to login again');
        TokenManager.clearTokens();
        
        // Create a special error to indicate session expired
        const sessionError = new Error('Your session has expired. Please login again.');
        sessionError.status = 401;
        sessionError.isSessionExpired = true;
        sessionError.data = data;
        throw sessionError;
      }
    }
    
    // Check for limit exceeded error
    if (response.status === 429 || response.status === 403 || response.status === 402) {
      const isLimitError = message && (
        message.toLowerCase().includes('limit') ||
        message.toLowerCase().includes('quota') ||
        message.toLowerCase().includes('exceeded')
      );
      
      if (isLimitError) {
        const limitError = new Error('You have reached your limit. Please upgrade to premium for unlimited access.');
        limitError.isLimitError = true;
        limitError.status = response.status;
        limitError.data = data;
        throw limitError;
      }
    }
    
    const error = new Error(message);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}


