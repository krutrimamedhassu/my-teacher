import React from 'react';
import { Box, Typography, Button } from '@mui/material';

const SecuritySection = ({ onOpenPassword, onOpenEmail, onLogout }) => {
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 2, borderBottom: '1px solid #e0e0e0' }}>
        <Typography variant="body1" sx={{ fontWeight: 500 }}>
          Change password
        </Typography>
        <Button 
          variant="outlined" 
          onClick={onOpenPassword} 
          size="small"
          sx={{
            borderColor: '#999',
            color: '#666',
            '&:hover': {
              borderColor: '#666',
              backgroundColor: 'rgba(0, 0, 0, 0.04)'
            }
          }}
        >
          Change password
        </Button>
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 2, borderBottom: '1px solid #e0e0e0' }}>
        <Typography variant="body1" sx={{ fontWeight: 500 }}>
          Change email
        </Typography>
        <Button 
          variant="outlined" 
          onClick={onOpenEmail} 
          size="small"
          sx={{
            borderColor: '#999',
            color: '#666',
            '&:hover': {
              borderColor: '#666',
              backgroundColor: 'rgba(0, 0, 0, 0.04)'
            }
          }}
        >
          Change email
        </Button>
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 2 }}>
        <Typography variant="body1" sx={{ fontWeight: 500 }}>
          Log out of this device
        </Typography>
        <Button 
          variant="outlined" 
          onClick={onLogout} 
          size="small"
          sx={{
            borderColor: '#999',
            color: '#666',
            '&:hover': {
              borderColor: '#666',
              backgroundColor: 'rgba(0, 0, 0, 0.04)'
            }
          }}
        >
          Log out
        </Button>
      </Box>
    </Box>
  );
};

export default SecuritySection;


