import React from 'react';
import { Box, Typography, FormControl, Select, MenuItem, Switch } from '@mui/material';

const GeneralSection = ({ streamingMode = 'traditional', showRightSidebar = true, onChangeSetting }) => {
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 2, borderBottom: '1px solid #e0e0e0' }}>
        <Typography variant="body1" sx={{ fontWeight: 500 }}>
          Streaming Mode
        </Typography>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <Select
            variant="outlined"
            value={streamingMode}
            onChange={(e) => onChangeSetting('streamingMode', e.target.value)}
          >
            <MenuItem value="traditional">Traditional</MenuItem>
            <MenuItem value="streaming">Streaming</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 2.5, borderBottom: '1px solid #e0e0e0' }}>
        <Box sx={{ flex: 1 }}>
          <Typography variant="body1" sx={{ fontWeight: 600, color: '#1a1a1a' }}>
            Chat Sidebar
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Typography variant="caption" sx={{ color: showRightSidebar ? '#666' : '#999', fontSize: '0.75rem', fontWeight: 500 }}>
            {showRightSidebar ? 'Visible' : 'Hidden'}
          </Typography>
          <Switch
            checked={showRightSidebar}
            onChange={(e) => onChangeSetting('showRightSidebar', e.target.checked)}
            sx={{
              width: 42,
              height: 24,
              padding: 0,
              display: 'flex',
              alignItems: 'center',
              '& .MuiSwitch-switchBase': {
                padding: 0,
                margin: '2px',
                transform: 'translateX(0px)',
                '&.Mui-checked': {
                  transform: 'translateX(18px)',
                  '& + .MuiSwitch-track': {
                    backgroundColor: '#000',
                    opacity: 1,
                  },
                },
              },
              '& .MuiSwitch-thumb': {
                width: 20,
                height: 20,
                borderRadius: '50%',
                backgroundColor: '#fff',
                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.15)',
              },
              '& .MuiSwitch-track': {
                width: 42,
                height: 24,
                borderRadius: 12,
                backgroundColor: '#e0e0e0',
                opacity: 1,
                transition: 'background-color 200ms ease-in-out',
              },
            }}
          />
        </Box>
      </Box>
    </Box>
  );
};

export default GeneralSection;


