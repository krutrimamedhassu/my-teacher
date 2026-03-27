import React, { createContext, useContext, useState, useEffect } from 'react';
import { getCurrentUser, logout, checkAuthentication } from '../services';
import { TokenManager } from '../utils/apiRequest';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const fetchUser = async () => {
    try {
      const isAuth = await checkAuthentication();
      if (isAuth) {
        // Check if token is expired before making API call
        if (TokenManager.isAccessTokenExpired()) {
          try {
            await TokenManager.refreshAccessToken();
          } catch (refreshError) {
            console.log('🔐 AuthContext: Token refresh failed during auth check, logging out');
            setUser(null);
            setIsAuthenticated(false);
            TokenManager.clearTokens();
            setLoading(false);
            return;
          }
        }
        
        const userData = await getCurrentUser();
        setUser(userData);
        setIsAuthenticated(true);
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (error) {
      // Handle session expired errors
      if (error?.isSessionExpired) {
        console.log('🔐 AuthContext: Session expired, logging out user');
        setUser(null);
        setIsAuthenticated(false);
        TokenManager.clearTokens();
      } else {
        // Don't log errors for initial auth check - this is expected when not logged in
        setUser(null);
        setIsAuthenticated(false);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  // Periodic token refresh - check every 5 minutes and refresh if token expires in next 10 minutes
  useEffect(() => {
    if (!isAuthenticated) return;

    const interval = setInterval(async () => {
      if (TokenManager.isAuthenticated()) {
        const token = TokenManager.getAccessToken();
        if (token) {
          try {
            // Check if token expires in the next 10 minutes (600 seconds)
            const payload = JSON.parse(atob(token.split('.')[1]));
            const currentTime = Math.floor(Date.now() / 1000);
            const timeUntilExpiry = payload.exp - currentTime;
            
            if (timeUntilExpiry < 600) { // Less than 10 minutes left
              console.log('🔄 AuthContext: Token expires soon, proactively refreshing');
              await TokenManager.refreshAccessToken();
            }
          } catch (error) {
            console.warn('⚠️ AuthContext: Failed to check or refresh token:', error);
            // If refresh fails, the user will be logged out on next API call
          }
        }
      }
    }, 5 * 60 * 1000); // Check every 5 minutes

    return () => clearInterval(interval);
  }, [isAuthenticated]);

  const login = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
  };

  const logoutUser = async (isSessionExpired = false) => {
    try {
      await logout();
    } catch (error) {
      console.error('Error during logout:', error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      
      // Don't clear anon_user_id - we'll need it for anonymous chat session
      // The ChatPage component will handle creating a new anonymous conversation
      
      // If session expired, show a more prominent notification
      if (isSessionExpired) {
        console.log('🔐 Session expired - user logged out');
        // You could show a toast notification here if you have one
      }
      
      // Only redirect from truly protected routes (not chat which allows anonymous)
      if (window.location.pathname.startsWith('/explore') || 
          window.location.pathname.startsWith('/contact')) {
        window.location.href = '/login';
      }
    }
  };

  const updateUser = (userData) => {
    setUser(userData);
  };

  // Global session expiration handler
  const handleSessionExpired = () => {
    console.log('🚨 AuthContext: Global session expiration handler called');
    logoutUser(true);
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    logout: logoutUser,
    updateUser,
    refreshUser: fetchUser,
    handleSessionExpired
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 