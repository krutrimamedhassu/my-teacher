import React, { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Button,
  Typography,
  Alert,
  useTheme,
} from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import { loginUser, registerUser } from '../services';
import LoginSection from './auth/LoginSection';
import RegisterSection from './auth/RegisterSection';
import ForgotSection from './auth/ForgotSection';
import { useAuth } from '../contexts/AuthContext';

const AuthPage = () => {
  const theme = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const { login, refreshUser } = useAuth();

  const initialMode = useMemo(() => {
    if (location.pathname.includes('register')) return 'register';
    if (location.pathname.includes('forgot')) return 'forgot';
    return 'login';
  }, [location.pathname]);

  const [mode, setMode] = useState(initialMode); // 'login' | 'register' | 'forgot'
  useEffect(() => setMode(initialMode), [initialMode]);

  // Login state
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [loginStep, setLoginStep] = useState('email');

  // Register state
  const [registerData, setRegisterData] = useState({
    fullName: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [showRegisterPassword, setShowRegisterPassword] = useState(false);
  const [showRegisterConfirmPassword, setShowRegisterConfirmPassword] = useState(false);

  // Forgot state
  const [forgotEmail, setForgotEmail] = useState('');

  // Common UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Helpers for password strength (from RegisterPage)
  const validatePassword = (password) => {
    const feedback = [];
    let score = 0;
    if (password.length >= 8) score += 1; else feedback.push('At least 8 characters');
    if (/[a-z]/.test(password)) score += 1; else feedback.push('At least one lowercase letter');
    if (/[A-Z]/.test(password)) score += 1; else feedback.push('At least one uppercase letter');
    if (/[0-9]/.test(password)) score += 1; else feedback.push('At least one number');
    if (/[^A-Za-z0-9]/.test(password)) score += 1; else feedback.push('At least one special character');
    return { score, feedback };
  };
  const passwordStrength = useMemo(() => validatePassword(registerData.password || ''), [registerData.password]);
  const getPasswordStrengthColor = (score) => {
    if (score <= 2) return 'error';
    if (score <= 3) return 'warning';
    if (score <= 4) return 'info';
    return 'success';
  };
  const getPasswordStrengthText = (score) => {
    if (score <= 2) return 'Weak';
    if (score <= 3) return 'Fair';
    if (score <= 4) return 'Good';
    return 'Strong';
  };

  // Actions
  const handleLoginEmailContinue = (e) => {
    e.preventDefault();
    if (!loginData.email) return setError('Please enter your email address');
    if (!loginData.email.includes('@')) return setError('Please enter a valid email address');
    setError('');
    setLoginStep('password');
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      if (!loginData.email || !loginData.email.includes('@')) {
        setError('Please enter a valid email address');
        setLoading(false);
        return;
      }
      if (!loginData.password) {
        setError('Please enter your password');
        setLoading(false);
        return;
      }
      const response = await loginUser(loginData.email, loginData.password);
      setSuccess('Login successful! Redirecting...');
      if (response.user) {
        localStorage.setItem('user', JSON.stringify(response.user));
        login(response.user);
        try { await refreshUser(); } catch (_) {}
      }
      setTimeout(() => navigate('/chat'), 800);
    } catch (err) {
      setError(err?.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const errors = [];
      if (!registerData.fullName.trim()) errors.push('Full name is required');
      if (!registerData.username.trim() || registerData.username.length < 3) errors.push('Username must be at least 3 characters long');
      if (!registerData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerData.email)) errors.push('Please enter a valid email address');
      if (!registerData.password) errors.push('Password is required');
      if (passwordStrength.score < 3) errors.push('Password is too weak');
      if (registerData.password !== registerData.confirmPassword) errors.push('Passwords do not match');
      if (errors.length) {
        setError(errors.join(', '));
        setLoading(false);
        return;
      }

      const response = await registerUser({
        fullName: registerData.fullName,
        username: registerData.username,
        email: registerData.email,
        password: registerData.password
      });
      setSuccess('Registration successful! Redirecting to login...');
      if (response.user) {
        localStorage.setItem('user', JSON.stringify(response.user));
      }
      setTimeout(() => setMode('login'), 1200);
    } catch (err) {
      setError(err?.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      if (!forgotEmail || !forgotEmail.includes('@')) {
        setError('Please enter a valid email address');
        setLoading(false);
        return;
      }
      // Simulate request
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSuccess('Password reset instructions have been sent to your email address.');
    } catch (err) {
      setError(err?.message || 'Failed to send password reset email.');
    } finally {
      setLoading(false);
    }
  };

  // Layout
  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', flex: 1 }}>
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
          <Box sx={{ position: 'absolute', top: 20, left: 24 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, color: '#000', fontSize: '18px' }}>
              {process.env.REACT_APP_HEADER_TITLE}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'flex-start', flex: 1, width: '100%', pl: 0 }}>
            <Typography variant="h2" sx={{ color: '#1976d2', fontWeight: 700, fontSize: { xs: '32px', md: '42px' }, lineHeight: 1.1, mb: 1 }}>
              {process.env.REACT_APP_HERO_LINE1}
            </Typography>
            <Typography variant="h3" sx={{ color: '#1976d2', fontWeight: 500, fontSize: { xs: '24px', md: '32px' }, lineHeight: 1.1 }}>
              {process.env.REACT_APP_HERO_LINE2}
            </Typography>
          </Box>
        </Box>

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
          <Box sx={{ width: '100%', maxWidth: 460 }}>
            <Typography variant="h4" sx={{ color: '#000', fontWeight: 600, fontSize: '24px', textAlign: 'center', mb: 4 }}>
              {mode === 'login' && 'Welcome back'}
              {mode === 'register' && 'Create Account'}
              {mode === 'forgot' && 'Reset Password'}
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
            )}
            {success && (
              <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>
            )}

            {mode === 'login' && (
              <LoginSection
                loginData={loginData}
                onLoginDataChange={setLoginData}
                showPassword={showPassword}
                onToggleShowPassword={() => setShowPassword(v => !v)}
                loginStep={loginStep}
                onContinueEmail={handleLoginEmailContinue}
                onSubmit={handleLoginSubmit}
                loading={loading}
                onSwitchToForgot={() => { setMode('forgot'); setError(''); setSuccess(''); }}
                clearError={() => setError('')}
              />
            )}

            {mode === 'register' && (
              <Card sx={{ boxShadow: 'none' }}>
                <CardContent sx={{ p: 0 }}>
                  <RegisterSection
                    data={registerData}
                    onChange={setRegisterData}
                    onSubmit={handleRegisterSubmit}
                    loading={loading}
                    showPassword={showRegisterPassword}
                    onToggleShowPassword={() => setShowRegisterPassword(v => !v)}
                    showConfirmPassword={showRegisterConfirmPassword}
                    onToggleShowConfirmPassword={() => setShowRegisterConfirmPassword(v => !v)}
                    strength={passwordStrength}
                    strengthColor={getPasswordStrengthColor}
                    strengthText={getPasswordStrengthText}
                    clearError={() => setError('')}
                  />
                </CardContent>
              </Card>
            )}

            {mode === 'forgot' && (
              <Card sx={{ boxShadow: 'none' }}>
                <CardContent sx={{ p: 0 }}>
                  <ForgotSection
                    email={forgotEmail}
                    onChange={setForgotEmail}
                    onSubmit={handleForgotSubmit}
                    loading={loading}
                    onBack={() => { setMode('login'); setError(''); setSuccess(''); setLoginStep('email'); }}
                    clearError={() => setError('')}
                  />
                </CardContent>
              </Card>
            )}

            {/* Mode Switchers */}
            {mode !== 'register' && (
              <Box sx={{ textAlign: 'center', mt: 3 }}>
                <Typography variant="body2" sx={{ color: '#666', mb: 0.5 }}>
                  Don't have an account?
                </Typography>
                <Box>
                  <Button onClick={() => { setMode('register'); setError(''); setSuccess(''); }} variant="text" sx={{ color: theme.palette.primary.main, textTransform: 'none', fontSize: '14px', fontWeight: 500, p: 0, minWidth: 0 }}>
                    Sign up
                  </Button>
                  <Typography component="span" sx={{ mx: 1, color: '#999' }}>|</Typography>
                  <Button onClick={() => navigate('/chat')} variant="text" sx={{ color: theme.palette.primary.main, textTransform: 'none', fontSize: '14px', fontWeight: 500, p: 0, minWidth: 0 }}>
                    Try it now
                  </Button>
                </Box>
              </Box>
            )}
            {mode === 'register' && (
              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <Typography variant="body2" sx={{ color: '#666', mb: 0.5 }}>
                  Already have an account?
                </Typography>
                <Box>
                  <Button onClick={() => { setMode('login'); setError(''); setSuccess(''); setLoginStep('email'); }} variant="text" sx={{ color: theme.palette.primary.main, textTransform: 'none', fontSize: '14px', fontWeight: 500, p: 0, minWidth: 0 }}>
                    Sign in
                  </Button>
                  <Typography component="span" sx={{ mx: 1, color: '#999' }}>|</Typography>
                  <Button onClick={() => navigate('/chat')} variant="text" sx={{ color: theme.palette.primary.main, textTransform: 'none', fontSize: '14px', fontWeight: 500, p: 0, minWidth: 0 }}>
                    Try it now
                  </Button>
                </Box>
              </Box>
            )}

            
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default AuthPage;


