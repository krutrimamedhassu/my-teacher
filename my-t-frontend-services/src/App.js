import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, responsiveFontSizes } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import GlobalStyles from '@mui/material/GlobalStyles';

// Import AuthProvider
import { AuthProvider } from './contexts/AuthContext';
import { SettingsProvider } from './contexts/SettingsContext';
import { ApiKeyProvider } from './contexts/ApiKeyContext';

// Import components
import ProtectedRoute from './components/ProtectedRoute';

// Import pages
import ContactPage from './pages/ContactPage';
import ExplorePage from './pages/ExplorePage';
import ChatPage from './pages/ChatPage';
import AuthPage from './pages/AuthPage';
import IndexPage from './pages/IndexPage';

// Import test helper for development
import './utils/tokenTestHelper';

// Create MUI theme
let theme = createTheme({
  palette: {
    primary: {
      light: '#4dabf5',
      main: '#1976d2', // Primary color as specified in requirements
      dark: '#1565c0',
      contrastText: '#fff',
    },
    secondary: {
      light: '#33eb91',
      main: '#00c853',
      dark: '#00a040',
      contrastText: '#fff',
    },
    background: {
      default: '#f8f9fa',
      paper: '#ffffff',
    },
    text: {
      primary: '#212121',
      secondary: '#616161',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
    },
    h2: {
      fontWeight: 600,
    },
    h3: {
      fontWeight: 600,
    },
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 500,
    },
    h6: {
      fontWeight: 500,
    },
    subtitle1: {
      fontWeight: 500,
    },
    button: {
      fontWeight: 500,
      textTransform: 'none',
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
        },
        contained: {
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          '&:hover': {
            boxShadow: '0 6px 10px rgba(0,0,0,0.15)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        rounded: {
          borderRadius: 12,
        },
        elevation1: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        },
        elevation2: {
          boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
        },
        elevation3: {
          boxShadow: '0 6px 16px rgba(0,0,0,0.1)',
        },
      },
    },
  },
});

// Make typography responsive
theme = responsiveFontSizes(theme);

// Global styles
const globalStyles = {
  // Subtle animations for links and interactive elements (but not form inputs)
  'a, button, .MuiButtonBase-root': {
    transition: 'all 0.2s ease-in-out !important',
  },
  // Prevent form fields and containers from animating on focus
  '.MuiTextField-root, .MuiFormControl-root, .MuiInputBase-root, .MuiCard-root .MuiTextField-root': {
    transition: 'none !important',
    transform: 'none !important',
  },
  // Prevent parent containers from moving when inputs are focused
  '.MuiCard-root:has(.MuiTextField-root:focus), .MuiCard-root:has(.MuiInputBase-root:focus)': {
    transform: 'none !important',
    transition: 'none !important',
  },
  // Improve link hover states
  'a:hover, button:hover': {
    opacity: 0.85,
  },
  // Add subtle hover effect to cards (but not form cards)
  '.MuiCard-root:not(:has(.MuiTextField-root))': {
    transition: 'transform 0.3s ease, box-shadow 0.3s ease',
  },
  '.MuiCard-root:not(:has(.MuiTextField-root)):hover': {
    transform: 'translateY(-4px)',
    boxShadow: '0 8px 16px rgba(0,0,0,0.1)',
  },
  // Disable global focus styles - let CSS handle focus states
  'a:focus, button:focus, input:focus, textarea:focus': {
    outline: 'none',
    boxShadow: 'none',
    transform: 'none !important',
  },
  // Prevent any form-related elements from causing layout shifts
  'input:focus, textarea:focus, .MuiTextField-root:focus-within': {
    scrollMarginTop: '0px !important',
    scrollMarginBottom: '0px !important',
  },
  // Hide the page-level scrollbar; inner overflow containers keep their own bars.
  html: {
    scrollBehavior: 'smooth',
    scrollbarWidth: 'none',
    msOverflowStyle: 'none',
  },
  body: {
    scrollbarWidth: 'none',
    msOverflowStyle: 'none',
  },
  'html::-webkit-scrollbar, body::-webkit-scrollbar': {
    display: 'none',
    width: 0,
    height: 0,
  },
  // Improve text selection
  '::selection': {
    backgroundColor: `${theme.palette.primary.main}33`,
    color: theme.palette.text.primary,
  },
};

function App() {
  useEffect(() => {
    document.title = 'My Teacher';
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline /> {/* Normalize CSS */}
      <GlobalStyles styles={globalStyles} />
      <AuthProvider>
        <SettingsProvider>
          <ApiKeyProvider>
            <Router>
              <Routes>
          <Route path="/" element={<Navigate to="/index" replace />} />
          {/* Public routes */}
          <Route path="/index" element={<IndexPage />} />
          <Route path="/login" element={<AuthPage />} />
          <Route path="/register" element={<AuthPage />} />
          <Route path="/forgot-password" element={<AuthPage />} />
          
          {/* Protected routes */}
          <Route path="/" element={
            <ProtectedRoute allowAnonymous={true}>
              <ChatPage />
            </ProtectedRoute>
          } />
          <Route path="/chat/:conversationId" element={
            <ProtectedRoute allowAnonymous={true}>
              <ChatPage />
            </ProtectedRoute>
          } />
          <Route path="/chat" element={
            <ProtectedRoute allowAnonymous={true}>
              <ChatPage />
            </ProtectedRoute>
          } />
          <Route path="/contact" element={
            <ProtectedRoute>
              <ContactPage />
            </ProtectedRoute>
          } />
          <Route path="/explore" element={
            <ProtectedRoute>
              <ExplorePage />
            </ProtectedRoute>
          } />
          
        </Routes>
        </Router>
        </ApiKeyProvider>
        </SettingsProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}


export default App;