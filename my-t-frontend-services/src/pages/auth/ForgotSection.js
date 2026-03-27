import React, { useState } from 'react';
import { Box, TextField, Button, useTheme } from '@mui/material';
import { ArrowBack } from '@mui/icons-material';

const ForgotSection = ({
  email,
  onChange,
  onSubmit,
  loading,
  onBack,
  clearError
}) => {
  const [emailFocused, setEmailFocused] = useState(false);
  const theme = useTheme();

  return (
    <Box component="form" onSubmit={onSubmit}>
      <TextField
        fullWidth
        label={emailFocused || (email && email.length > 0) ? 'Email' : 'Enter your email'}
        type="email"
        value={email}
        onChange={(e) => { onChange(e.target.value); if (clearError) clearError(); }}
        onFocus={() => setEmailFocused(true)}
        onBlur={() => setEmailFocused(false)}
        margin="normal"
        required
        sx={{
          '& .MuiOutlinedInput-root': { borderRadius: '12px', height: '56px', fontSize: '16px', '&:hover fieldset': { borderColor: theme.palette.primary.main } },
          '& .MuiInputLabel-root': { fontSize: '16px' },
          '& input': { backgroundColor: 'transparent' },
          '& input:-webkit-autofill': { WebkitBoxShadow: '0 0 0 1000px #fff inset', WebkitTextFillColor: '#000', caretColor: '#000', transition: 'background-color 9999s ease-in-out 0s' }
        }}
      />
      <Button
        type="submit"
        fullWidth
        variant="contained"
        disabled={loading}
        sx={{
          mt: 2,
          mb: 1,
          py: 2,
          borderRadius: '12px',
          fontSize: '16px',
          fontWeight: 600,
          backgroundColor: theme.palette.primary.main,
          color: 'white',
          textTransform: 'none',
          height: '56px',
          '&:hover': { backgroundColor: theme.palette.primary.dark }
        }}
      >
        {loading ? 'Sending...' : 'Send Reset Instructions'}
      </Button>
      <Box sx={{ textAlign: 'center', mt: 2 }}>
        <Button onClick={onBack} variant="text" size="small" sx={{ textTransform: 'none' }}>
          <ArrowBack sx={{ mr: 1, fontSize: 16 }} /> Back to Sign In
        </Button>
      </Box>
    </Box>
  );
};

export default ForgotSection;


