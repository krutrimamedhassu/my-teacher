import React from 'react';
import { Link } from 'react-router-dom';
import { Box, Typography, Button } from '@mui/material';
import { useAuth } from '../../contexts/AuthContext';

const Footer = () => {
  const { isAuthenticated } = useAuth();

  const featureLinks = [
    { label: 'AI Chat', path: '/chat' },
    { label: 'Text to Speech', path: '/speech' },
    { label: 'Topic Breakdown', path: '/breakdown' },
    { label: 'Key Concepts', path: '/key-concepts' },
  ];

  const resourceLinks = [
    { label: 'Documentation', path: '/contact' },
    { label: 'API Reference', path: '/contact' },
    { label: 'Help Center', path: '/contact' },
    { label: 'Community', path: '/contact' },
    { label: 'Status', path: '/contact' },
  ];

  const companyLinks = [
    { label: 'About Us', path: '/contact' },
    { label: 'Careers', path: '/contact' },
    { label: 'Privacy Policy', path: '/contact' },
    { label: 'Terms of Service', path: '/contact' },
    { label: 'Contact', path: '/contact' },
  ];

  return (
    <Box
      component="footer"
      sx={{
        backgroundColor: 'white',
        py: 4,
        px: 4,
        mt: 6,
      }}
    >
      <Box
        sx={{
          maxWidth: '1200px',
          mx: 'auto',
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: '2fr 1fr 1fr 1fr' },
          gap: 4,
        }}
      >
        {/* Brand Section */}
        <Box>
          <Typography
            variant="h6"
            sx={{
              fontWeight: 600,
              color: '#000',
              fontSize: '18px',
              mb: 2,
            }}
          >
            {process.env.REACT_APP_FOOTER_TITLE}
          </Typography>
          <Typography
            sx={{
              fontSize: '14px',
              lineHeight: 1.6,
              color: '#666',
              mb: 3,
              maxWidth: '280px',
            }}
          >
            {process.env.REACT_APP_FOOTER_DESCRIPTION}
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              component={Link}
              to="/chat"
              variant="contained"
              size="small"
              sx={{
                backgroundColor: '#000',
                color: 'white',
                borderRadius: '6px',
                textTransform: 'none',
                fontSize: '14px',
                '&:hover': {
                  backgroundColor: '#333',
                },
              }}
            >
              Try Now
            </Button>
            {!isAuthenticated && (
              <Button
                component={Link}
                to="/login"
                variant="outlined"
                size="small"
                sx={{
                  borderColor: '#e0e0e0',
                  color: '#666',
                  borderRadius: '6px',
                  textTransform: 'none',
                  fontSize: '14px',
                  '&:hover': {
                    backgroundColor: '#f5f5f5',
                  },
                }}
              >
                Sign In
              </Button>
            )}
          </Box>
        </Box>

        {/* Product Links */}
        <Box>
          <Typography
            variant="subtitle2"
            sx={{
              fontWeight: 600,
              color: '#000',
              fontSize: '14px',
              mb: 2,
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            Features
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {featureLinks.map((item) => (
              <Typography
                key={item.label}
                component={Link}
                to={item.path}
                sx={{
                  fontSize: '14px',
                  color: '#666',
                  textDecoration: 'none',
                  '&:hover': {
                    color: '#1976d2',
                    textDecoration: 'underline',
                  },
                }}
              >
                {item.label}
              </Typography>
            ))}
          </Box>
        </Box>

        {/* Resources Links */}
        <Box>
          <Typography
            variant="subtitle2"
            sx={{
              fontWeight: 600,
              color: '#000',
              fontSize: '14px',
              mb: 2,
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            Resources
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {resourceLinks.map((item) => (
              <Typography
                key={item.label}
                component={Link}
                to={item.path}
                sx={{
                  fontSize: '14px',
                  color: '#666',
                  textDecoration: 'none',
                  '&:hover': {
                    color: '#1976d2',
                    textDecoration: 'underline',
                  },
                }}
              >
                {item.label}
              </Typography>
            ))}
          </Box>
        </Box>

        {/* Company Links */}
        <Box>
          <Typography
            variant="subtitle2"
            sx={{
              fontWeight: 600,
              color: '#000',
              fontSize: '14px',
              mb: 2,
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            Company
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {companyLinks.map((item) => (
              <Typography
                key={item.label}
                component={Link}
                to={item.path}
                sx={{
                  fontSize: '14px',
                  color: '#666',
                  textDecoration: 'none',
                  '&:hover': {
                    color: '#1976d2',
                    textDecoration: 'underline',
                  },
                }}
              >
                {item.label}
              </Typography>
            ))}
          </Box>
        </Box>
      </Box>

      {/* Bottom Bar */}
      <Box
        sx={{
          maxWidth: '1200px',
          mx: 'auto',
          pt: 3,
          mt: 4,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 2,
        }}
      >
        <Typography
          sx={{
            fontSize: '14px',
            color: '#666',
          }}
        >
          © 2025 {process.env.REACT_APP_FOOTER_TITLE}. All rights reserved.
        </Typography>
        <Typography
          sx={{
            fontSize: '14px',
            color: '#666',
          }}
        >
          Made with ❤️ for learners everywhere
        </Typography>
      </Box>
    </Box>
  );
};

export default Footer;