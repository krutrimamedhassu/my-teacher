import React, { useState } from 'react';
import { Box, TextField, Button, InputAdornment, IconButton, CircularProgress, useTheme } from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';

const LoginSection = ({
  loginData,
  onLoginDataChange,
  showPassword,
  onToggleShowPassword,
  loginStep,
  onContinueEmail,
  onSubmit,
  loading,
  onSwitchToForgot,
  clearError
}) => {
  const theme = useTheme();
  const [emailFocused, setEmailFocused] = useState(false);

  return (
    <Box component="form" onSubmit={loginStep === 'email' ? onContinueEmail : onSubmit} sx={{ mb: 3 }}>
      <TextField
        fullWidth
        label={emailFocused || (loginData.email && loginData.email.length > 0) ? 'Email' : 'Enter your email'}
        name="email"
        type="email"
        value={loginData.email}
        onChange={(e) => { onLoginDataChange({ ...loginData, email: e.target.value }); if (clearError) clearError(); }}
        onFocus={() => setEmailFocused(true)}
        onBlur={() => setEmailFocused(false)}
        margin="normal"
        required
        autoFocus={loginStep === 'email'}
        sx={{
          mb: 3,
          '& .MuiOutlinedInput-root': { borderRadius: '12px', height: '56px', fontSize: '16px', '&:hover fieldset': { borderColor: theme.palette.primary.main } },
          '& .MuiInputLabel-root': { fontSize: '16px' },
          '& input': { backgroundColor: 'transparent' },
          '& input:-webkit-autofill': {
            WebkitBoxShadow: '0 0 0 1000px #fff inset',
            WebkitTextFillColor: '#000',
            caretColor: '#000',
            transition: 'background-color 9999s ease-in-out 0s'
          }
        }}
      />

      {loginStep === 'password' && (
        <>
          <TextField
            fullWidth
            label="Enter your password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            value={loginData.password}
            onChange={(e) => { onLoginDataChange({ ...loginData, password: e.target.value }); if (clearError) clearError(); }}
            margin="normal"
            required
            autoFocus
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={onToggleShowPassword} edge="end" size="small">
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
            sx={{
              mb: 1.5,
            '& .MuiOutlinedInput-root': { borderRadius: '12px', height: '56px', fontSize: '16px', '&:hover fieldset': { borderColor: theme.palette.primary.main } },
            '& .MuiInputLabel-root': { fontSize: '16px' },
            '& input': { backgroundColor: 'transparent' },
            '& input:-webkit-autofill': {
              WebkitBoxShadow: '0 0 0 1000px #fff inset',
              WebkitTextFillColor: '#000',
              caretColor: '#000',
              transition: 'background-color 9999s ease-in-out 0s'
            }
            }}
          />
          <Box sx={{ textAlign: 'left', mb: 3 }}>
            <Button onClick={onSwitchToForgot} variant="text" size="small" sx={{ color: '#1976d2', textTransform: 'none', p: 0, minWidth: 0 }}>
              Forgot password?
            </Button>
          </Box>
        </>
      )}

      <Button
        type="submit"
        fullWidth
        variant="contained"
        disabled={loginStep === 'password' && loading}
        sx={{
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
        {loginStep === 'email' ? 'Continue' : (loading ? <CircularProgress size={24} color="inherit" /> : 'Continue to login')}
      </Button>
    </Box>
  );
};

export default LoginSection;


