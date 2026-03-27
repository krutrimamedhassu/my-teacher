import React from 'react';
import { Link } from 'react-router-dom';
import { Box, Typography, Button, IconButton } from '@mui/material';
import { Search } from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';

const Header = ({ isVisible = true, onProfileClick }) => {
  const { isAuthenticated, user } = useAuth();

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        height: 60,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        px: 3,
        backgroundColor: 'white',
        zIndex: 1000,
        transform: isVisible ? 'translateY(0)' : 'translateY(-100%)',
        transition: 'transform 0.3s ease-in-out',
      }}
    >
      {/* Logo Section */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography
          component={Link}
          to="/"
          variant="h6"
          sx={{
            fontWeight: 600,
            color: '#000',
            fontSize: '18px',
            textDecoration: 'none',
            '&:hover': {
              color: '#1976d2',
            },
          }}
        >
{process.env.REACT_APP_HEADER_TITLE}
        </Typography>
      </Box>

      {/* Right Section */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton size="small">
          <Search />
        </IconButton>
        <Button
          component={isAuthenticated ? undefined : Link}
          to={isAuthenticated ? undefined : "/login"}
          onClick={isAuthenticated ? onProfileClick : undefined}
          variant="outlined"
          sx={{
            borderRadius: '20px',
            textTransform: 'none',
            color: '#000',
            borderColor: '#e0e0e0',
            backgroundColor: 'white',
            '&:hover': {
              backgroundColor: '#f5f5f5',
            },
          }}
        >
          {isAuthenticated ? (user?.username || 'Profile') : 'Log in'}
        </Button>
      </Box>
    </Box>
  );
};

export default Header;