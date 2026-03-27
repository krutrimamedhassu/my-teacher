import React, { useState, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { checkAuthentication } from '../services';
import { CircularProgress, Box } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

const ProtectedRoute = ({ children, allowAnonymous = false }) => {
  const location = useLocation();
  const { isAuthenticated: authContextAuthenticated, loading: authLoading } = useAuth();
  const [authenticated, setAuthenticated] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // First check the auth context
        if (authContextAuthenticated !== undefined) {
          setAuthenticated(authContextAuthenticated);
          setLoading(false);
          return;
        }
        
        // Fallback to API check
        const isAuth = await checkAuthentication();
        setAuthenticated(isAuth);
      } catch (error) {
        console.error('Authentication check failed:', error);
        setAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    if (!authLoading) {
      checkAuth();
    }
  }, [authContextAuthenticated, authLoading]);

  // Show loading spinner while checking authentication
  if (loading || authLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          background: '#f8f8f8',
        }}
      >
        <CircularProgress size={60} />
      </Box>
    );
  }

  // If route allows anonymous access, render children regardless of auth status
  if (allowAnonymous) {
    return children;
  }

  // For protected routes, check authentication
  if (!authenticated) {
    // Redirect to login page with the return url
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default ProtectedRoute; 