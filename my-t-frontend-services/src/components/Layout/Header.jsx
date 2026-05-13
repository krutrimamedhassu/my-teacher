import React from 'react';
import { Link } from 'react-router-dom';
import { Box, Typography, Button, IconButton } from '@mui/material';
import { Search } from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { fonts, ease, colors } from '../Landing/tokens';

// Scroll-aware header.
// When `overHero` is true the header sits on top of the dark hero with a
// transparent background and light text; once scrolled past the hero it
// flips to a white blurred backdrop with dark text. Other pages that don't
// pass `overHero` get the white-backdrop look by default.
const Header = ({ isVisible = true, onProfileClick, overHero = false }) => {
  const { isAuthenticated, user } = useAuth();

  const light = overHero;
  const fg = light ? '#f3f5fa' : colors.ink700;
  const fgHover = light ? '#ffffff' : colors.cobalt700;
  const bg = light ? 'transparent' : 'rgba(250, 250, 247, 0.78)';
  const borderColor = light ? 'rgba(255, 255, 255, 0.18)' : 'rgba(20, 30, 60, 0.1)';
  const buttonBorder = light ? 'rgba(255, 255, 255, 0.22)' : 'rgba(20, 30, 60, 0.14)';

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        height: 64,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        px: { xs: 2.5, md: 3.5 },
        backgroundColor: bg,
        backdropFilter: light ? 'none' : 'blur(12px) saturate(180%)',
        WebkitBackdropFilter: light ? 'none' : 'blur(12px) saturate(180%)',
        borderBottom: light ? '1px solid transparent' : `1px solid ${borderColor}`,
        zIndex: 1000,
        transform: isVisible ? 'translateY(0)' : 'translateY(-100%)',
        transition: `transform 300ms ${ease.outQuint}, background-color 300ms ${ease.outQuint}, border-color 300ms ${ease.outQuint}`,
        fontFamily: fonts.sans,
      }}
    >
      {/* Logo */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography
          component={Link}
          to="/"
          sx={{
            fontFamily: fonts.display,
            fontWeight: 400,
            color: fg,
            fontSize: 19,
            letterSpacing: '-0.01em',
            textDecoration: 'none',
            transition: `color 220ms ${ease.outQuint}`,
            '&:hover': { color: fgHover },
          }}
        >
          My Teacher
        </Typography>
      </Box>

      {/* Right side */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <IconButton
          size="small"
          sx={{
            color: fg,
            '&:hover': { color: fgHover, backgroundColor: light ? 'rgba(255,255,255,0.08)' : 'rgba(20,30,60,0.04)' },
          }}
        >
          <Search fontSize="small" />
        </IconButton>
        <Button
          component={isAuthenticated ? undefined : Link}
          to={isAuthenticated ? undefined : '/login'}
          onClick={isAuthenticated ? onProfileClick : undefined}
          variant="outlined"
          sx={{
            borderRadius: '999px',
            textTransform: 'none',
            fontFamily: fonts.sans,
            fontWeight: 500,
            fontSize: 14,
            letterSpacing: '-0.005em',
            color: fg,
            borderColor: buttonBorder,
            backgroundColor: light ? 'rgba(255, 255, 255, 0.04)' : '#ffffff',
            px: 2,
            '&:hover': {
              backgroundColor: light ? 'rgba(255, 255, 255, 0.12)' : 'rgba(20, 30, 60, 0.04)',
              borderColor: light ? 'rgba(255, 255, 255, 0.34)' : 'rgba(20, 30, 60, 0.22)',
            },
          }}
        >
          {isAuthenticated ? (user?.username || 'Profile') : 'Log in'}
        </Button>
      </Box>
    </Box>
  );
};

export default Header;
