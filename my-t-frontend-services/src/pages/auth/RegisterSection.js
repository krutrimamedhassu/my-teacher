import React, { useState } from 'react';
import { Box, TextField, Button, IconButton, Typography, LinearProgress, useTheme } from '@mui/material';
import { Visibility, VisibilityOff, CheckCircle, Cancel } from '@mui/icons-material';

const RegisterSection = ({
  data,
  onChange,
  onSubmit,
  loading,
  showPassword,
  onToggleShowPassword,
  showConfirmPassword,
  onToggleShowConfirmPassword,
  strength,
  strengthColor,
  strengthText,
  clearError
}) => {
  const [fullNameFocused, setFullNameFocused] = useState(false);
  const [usernameFocused, setUsernameFocused] = useState(false);
  const [emailFocused, setEmailFocused] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);
  const [confirmFocused, setConfirmFocused] = useState(false);
  const theme = useTheme();

  return (
    <Box component="form" onSubmit={onSubmit}>
      <TextField
        fullWidth
        label={fullNameFocused || (data.fullName && data.fullName.length > 0) ? 'Full name' : 'Enter your full name'}
        name="fullName"
        value={data.fullName}
        onChange={(e) => { onChange({ ...data, fullName: e.target.value }); if (clearError) clearError(); }}
        onFocus={() => setFullNameFocused(true)}
        onBlur={() => setFullNameFocused(false)}
        margin="normal"
        required
        sx={{
          '& .MuiOutlinedInput-root': { borderRadius: '12px', height: '56px', fontSize: '16px', '&:hover fieldset': { borderColor: theme.palette.primary.main } },
          '& input': { backgroundColor: 'transparent' },
          '& input:-webkit-autofill': { WebkitBoxShadow: '0 0 0 1000px #fff inset', WebkitTextFillColor: '#000', caretColor: '#000', transition: 'background-color 9999s ease-in-out 0s' }
        }}
      />
      <TextField
        fullWidth
        label={usernameFocused || (data.username && data.username.length > 0) ? 'Username' : 'Enter your username'}
        name="username"
        value={data.username}
        onChange={(e) => { onChange({ ...data, username: e.target.value }); if (clearError) clearError(); }}
        onFocus={() => setUsernameFocused(true)}
        onBlur={() => setUsernameFocused(false)}
        margin="normal"
        required
        sx={{
          '& .MuiOutlinedInput-root': { borderRadius: '12px', height: '56px', fontSize: '16px', '&:hover fieldset': { borderColor: theme.palette.primary.main } },
          '& input': { backgroundColor: 'transparent' },
          '& input:-webkit-autofill': { WebkitBoxShadow: '0 0 0 1000px #fff inset', WebkitTextFillColor: '#000', caretColor: '#000', transition: 'background-color 9999s ease-in-out 0s' }
        }}
      />
      <TextField
        fullWidth
        label={emailFocused || (data.email && data.email.length > 0) ? 'Email' : 'Enter your email'}
        name="email"
        type="email"
        value={data.email}
        onChange={(e) => { onChange({ ...data, email: e.target.value }); if (clearError) clearError(); }}
        onFocus={() => setEmailFocused(true)}
        onBlur={() => setEmailFocused(false)}
        margin="normal"
        required
        sx={{
          '& .MuiOutlinedInput-root': { borderRadius: '12px', height: '56px', fontSize: '16px', '&:hover fieldset': { borderColor: theme.palette.primary.main } },
          '& input': { backgroundColor: 'transparent' },
          '& input:-webkit-autofill': { WebkitBoxShadow: '0 0 0 1000px #fff inset', WebkitTextFillColor: '#000', caretColor: '#000', transition: 'background-color 9999s ease-in-out 0s' }
        }}
      />
      <TextField
        fullWidth
        label={passwordFocused || (data.password && data.password.length > 0) ? 'Password' : 'Enter your password'}
        name="password"
        type={showPassword ? 'text' : 'password'}
        value={data.password}
        onChange={(e) => { onChange({ ...data, password: e.target.value }); if (clearError) clearError(); }}
        onFocus={() => setPasswordFocused(true)}
        onBlur={() => setPasswordFocused(false)}
        margin="normal"
        required
        InputProps={{
          endAdornment: (
            <IconButton onClick={onToggleShowPassword} edge="end" size="small">
              {showPassword ? <VisibilityOff /> : <Visibility />}
            </IconButton>
          )
        }}
        sx={{
          '& .MuiOutlinedInput-root': { borderRadius: '12px', height: '56px', fontSize: '16px', '&:hover fieldset': { borderColor: theme.palette.primary.main } },
          '& input': { backgroundColor: 'transparent' },
          '& input:-webkit-autofill': { WebkitBoxShadow: '0 0 0 1000px #fff inset', WebkitTextFillColor: '#000', caretColor: '#000', transition: 'background-color 9999s ease-in-out 0s' }
        }}
      />
      {data.password && (
        <Box sx={{ mt: 1, mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>Password strength:</Typography>
            <Typography variant="body2" color={`${strengthColor(strength.score)}.main`} sx={{ fontWeight: 600 }}>{strengthText(strength.score)}</Typography>
          </Box>
          <LinearProgress variant="determinate" value={(strength.score / 5) * 100} color={strengthColor(strength.score)} sx={{ height: 6, borderRadius: 3 }} />
          {strength.feedback.length > 0 && (
            <Box sx={{ mt: 1 }}>
              {strength.feedback.map((fb) => (
                <Box key={`feedback-${fb}`} sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                  <Cancel sx={{ fontSize: 16, color: 'error.main', mr: 1 }} />
                  <Typography variant="caption" color="text.secondary">{fb}</Typography>
                </Box>
              ))}
            </Box>
          )}
        </Box>
      )}
      <TextField
        fullWidth
        label={confirmFocused || (data.confirmPassword && data.confirmPassword.length > 0) ? 'Confirm password' : 'Confirm your password'}
        name="confirmPassword"
        type={showConfirmPassword ? 'text' : 'password'}
        value={data.confirmPassword}
        onChange={(e) => { onChange({ ...data, confirmPassword: e.target.value }); if (clearError) clearError(); }}
        onFocus={() => setConfirmFocused(true)}
        onBlur={() => setConfirmFocused(false)}
        margin="normal"
        required
        InputProps={{
          endAdornment: (
            <IconButton onClick={onToggleShowConfirmPassword} edge="end" size="small">
              {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
            </IconButton>
          )
        }}
        sx={{
          '& .MuiOutlinedInput-root': { borderRadius: '12px', height: '56px', fontSize: '16px', '&:hover fieldset': { borderColor: theme.palette.primary.main } },
          '& input': { backgroundColor: 'transparent' },
          '& input:-webkit-autofill': { WebkitBoxShadow: '0 0 0 1000px #fff inset', WebkitTextFillColor: '#000', caretColor: '#000', transition: 'background-color 9999s ease-in-out 0s' }
        }}
      />
      {data.confirmPassword && (
        <Box sx={{ mt: 1, mb: 2 }}>
          {data.password === data.confirmPassword ? (
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <CheckCircle sx={{ fontSize: 16, color: 'success.main', mr: 1 }} />
              <Typography variant="caption" color="success.main">Passwords match</Typography>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Cancel sx={{ fontSize: 16, color: 'error.main', mr: 1 }} />
              <Typography variant="caption" color="error.main">Passwords do not match</Typography>
            </Box>
          )}
        </Box>
      )}
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
        {loading ? 'Creating...' : 'Create Account'}
      </Button>
    </Box>
  );
};

export default RegisterSection;


