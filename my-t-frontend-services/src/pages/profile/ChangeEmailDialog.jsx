import React from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, TextField, Button, IconButton, InputAdornment, CircularProgress } from '@mui/material';
import { Visibility, VisibilityOff, Close } from '@mui/icons-material';

const ChangeEmailDialog = ({ open, onClose, showEmailPassword, toggleShowPassword, emailData, onChange, onSave, saving }) => {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
          maxWidth: 480,
        }
      }}
    >
      <DialogTitle sx={{ 
        fontWeight: 600, 
        color: '#000', 
        fontSize: '1.25rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        pb: 2
      }}>
        Change Email
        <IconButton onClick={onClose} size="small">
          <Close />
        </IconButton>
      </DialogTitle>
      <DialogContent sx={{ pt: 1 }}>
        <TextField
          fullWidth
          label="Current Password"
          name="currentPassword"
          type={showEmailPassword ? 'text' : 'password'}
          value={emailData.currentPassword}
          onChange={onChange}
          margin="normal"
          required
          size="small"
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={toggleShowPassword} edge="end" size="small">
                  {showEmailPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
          sx={{ mb: 2 }}
        />
        <TextField
          fullWidth
          label="New Email Address"
          name="newEmail"
          type="email"
          value={emailData.newEmail}
          onChange={onChange}
          margin="normal"
          required
          size="small"
          sx={{ mb: 2 }}
        />
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 3, gap: 1 }}>
        <Button 
          onClick={onClose} 
          variant="outlined"
          size="small"
        >
          Cancel
        </Button>
        <Button
          onClick={onSave}
          variant="contained"
          disabled={saving}
          startIcon={saving ? <CircularProgress size={16} /> : null}
          size="small"
          sx={{
            bgcolor: '#000',
            color: '#fff',
            '&:hover': { 
              bgcolor: '#333' 
            },
          }}
        >
          {saving ? 'Updating...' : 'Update Email'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ChangeEmailDialog;


