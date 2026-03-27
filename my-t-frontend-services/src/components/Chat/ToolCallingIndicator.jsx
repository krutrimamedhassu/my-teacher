import React from 'react';
import { Box, Typography } from '@mui/material';

const ToolCallingIndicator = ({ toolName, theme }) => (
  <Box
    sx={{
      display: 'flex',
      justifyContent: 'flex-start',
      mb: 2,
      px: 2
    }}
  >
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        bgcolor: theme.palette.grey[100],
        borderRadius: 2,
        px: 2,
        py: 1
      }}
    >
      <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
        Calling {toolName} and you will see in right sidebar
      </Typography>
      <Box sx={{ display: 'flex', gap: 0.5, ml: 1 }}>
        <span className="typing-jump-dot">.</span>
        <span className="typing-jump-dot">.</span>
        <span className="typing-jump-dot">.</span>
      </Box>
    </Box>
  </Box>
);

export default ToolCallingIndicator; 