import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Link,
  Alert,
  IconButton,
  InputAdornment,
  CircularProgress,
  useTheme,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff

} from '@mui/icons-material';
import { useNavigate, Link as RouterLink, useLocation } from 'react-router-dom';
import { loginUser } from '../services';
import { useAuth } from '../contexts/AuthContext';

const LoginPage = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { login, refreshUser } = useAuth();
  
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [step, setStep] = useState('email'); // 'email' or 'password'

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (error) setError('');
  };

  const handleEmailContinue = (e) => {
    e.preventDefault();
    if (!formData.email) {
      setError('Please enter your email address');
      return;
    }
    if (!formData.email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }
    setError('');
    setStep('password');
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    if (!formData.email || !formData.email.includes('@')) {
      setError('Please enter a valid email address');
      setLoading(false);
      setStep('email');
      return;
    }

    if (!formData.password) {
      setError('Please enter your password');
      setLoading(false);
      return;
    }

    try {
      const response = await loginUser(formData.email, formData.password);
      setSuccess('Login successful! Redirecting...');
      
      if (response.user) {
        localStorage.setItem('user', JSON.stringify(response.user));
        // Update AuthContext immediately so UI (sidebars) reflects login without refresh
        login(response.user);
        // Optionally re-fetch from backend to ensure freshest user data
        try { await refreshUser(); } catch (_) {}
      }
      
      const from = location.state?.from?.pathname || '/chat';
      setTimeout(() => {
        navigate(from);
      }, 1000);
      
    } catch (error) {
      console.error('Login error:', error);
      setError(error.message || 'Login failed. Please check your credentials and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleTogglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Main Content Container */}
      <Box sx={{ display: 'flex', flex: 1 }}>
      {/* Left Side - Branding */}
      <Box
        sx={{
          flex: 1,
          backgroundColor: '#f0f8ff',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'flex-start',
          alignItems: 'flex-start',
          px: 8,
          py: 6,
          position: 'relative',
        }}
      >
        {/* Header in left column */}
        <Box
          sx={{
            position: 'absolute',
            top: 20,
            left: 24,
          }}
        >
          <Typography
            variant="h6"
            sx={{
              fontWeight: 600,
              color: '#000',
              fontSize: '18px',
            }}
          >
            My Teacher
          </Typography>
        </Box>

        {/* Main Content - Centered vertically */}
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          justifyContent: 'center', 
          alignItems: 'flex-start',
          flex: 1,
          width: '100%',
          pl: 0,
        }}>
          <Typography
            variant="h2"
            sx={{
              color: '#1976d2',
              fontWeight: 700,
              fontSize: { xs: '32px', md: '42px' },
              lineHeight: 1.1,
              mb: 1,
            }}
          >
            Learn anything.
          </Typography>
          <Typography
            variant="h3"
            sx={{
              color: '#1976d2',
              fontWeight: 500,
              fontSize: { xs: '24px', md: '32px' },
              lineHeight: 1.1,
            }}
          >
            Your AI tutor is ready.
          </Typography>
        </Box>
      </Box>

      {/* Right Side - Login Form */}
      <Box
        sx={{
          flex: 1,
          backgroundColor: 'white',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          px: 6,
          py: 6,
          position: 'relative',
        }}
      >
        <Box sx={{ width: '100%', maxWidth: '400px' }}>
          {/* Header */}
          <Typography
            variant="h4"
            sx={{
              color: '#000',
              fontWeight: 600,
              fontSize: '24px',
              textAlign: 'center',
              mb: 6,
            }}
          >
            How are you doing today?
          </Typography>

          {/* Error/Success Messages */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
          
          {success && (
            <Alert severity="success" sx={{ mb: 3 }}>
              {success}
            </Alert>
          )}

          {/* Unified Form: Email always visible and editable; Password appears after Continue */}
          <Box component="form" onSubmit={step === 'email' ? handleEmailContinue : handleLogin} sx={{ mb: 4 }}>
            {/* Email */}
            <TextField
              fullWidth
              label="Enter your email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleInputChange}
              margin="normal"
              required
              autoFocus={step === 'email'}
              sx={{
                mb: 3,
                '& .MuiOutlinedInput-root': {
                  borderRadius: '12px',
                  height: '56px',
                  fontSize: '16px',
                  '&:hover fieldset': {
                    borderColor: theme.palette.primary.main,
                  },
                },
                '& .MuiInputLabel-root': {
                  fontSize: '16px',
                },
              }}
            />

            {step === 'password' && (
              <>
                {/* Password */}
                <TextField
                  fullWidth
                  label="Enter your password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={handleInputChange}
                  margin="normal"
                  required
                  autoFocus
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={handleTogglePasswordVisibility}
                          edge="end"
                          size="small"
                        >
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    mb: 2,
                    '& .MuiOutlinedInput-root': {
                      borderRadius: '12px',
                      height: '56px',
                      fontSize: '16px',
                      '&:hover fieldset': {
                        borderColor: theme.palette.primary.main,
                      },
                    },
                    '& .MuiInputLabel-root': {
                      fontSize: '16px',
                    },
                  }}
                />

                {/* Forgot Password Link */}
                <Box sx={{ textAlign: 'left', mb: 3 }}>
                  <Link
                    component={RouterLink}
                    to="/forgot-password"
                    sx={{
                      color: '#1976d2',
                      textDecoration: 'none',
                      fontSize: '14px',
                      '&:hover': {
                        textDecoration: 'underline',
                      },
                    }}
                  >
                    Forgot password?
                  </Link>
                </Box>
              </>
            )}

            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={step === 'password' && loading}
              sx={{
                py: 2,
                borderRadius: '12px',
                fontSize: '16px',
                fontWeight: 600,
                backgroundColor: '#000',
                color: 'white',
                textTransform: 'none',
                height: '56px',
                '&:hover': {
                  backgroundColor: '#333',
                },
              }}
            >
              {step === 'email' ? (
                'Continue'
              ) : loading ? (
                <CircularProgress size={24} color="inherit" />
              ) : (
                'Continue to login'
              )}
            </Button>
          </Box>

          {/* Don't have an account */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>
              Don't have an account?
            </Typography>
            <Link
              component={RouterLink}
              to="/register"
              sx={{
                color: '#1976d2',
                textDecoration: 'none',
                fontSize: '16px',
                fontWeight: 500,
                '&:hover': {
                  textDecoration: 'underline',
                },
              }}
            >
              Sign up
            </Link>
          </Box>

          {/* Footer */}
          <Box sx={{ textAlign: 'center', mt: 'auto' }}>
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
              <Link
                href="#"
                sx={{
                  color: '#666',
                  fontSize: '12px',
                  textDecoration: 'none',
                  '&:hover': {
                    textDecoration: 'underline',
                  },
                }}
              >
                Terms of use
              </Link>
              <Typography sx={{ color: '#666', fontSize: '12px' }}>|</Typography>
              <Link
                href="#"
                sx={{
                  color: '#666',
                  fontSize: '12px',
                  textDecoration: 'none',
                  '&:hover': {
                    textDecoration: 'underline',
                  },
                }}
              >
                Privacy policy
              </Link>
            </Box>
          </Box>
        </Box>
      </Box>
      </Box>
    </Box>
  );
};

export default LoginPage;