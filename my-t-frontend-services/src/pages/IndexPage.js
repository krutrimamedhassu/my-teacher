import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Box, Typography, Button } from '@mui/material';
import { ArrowUpward } from '@mui/icons-material';
import ProfilePage from './ProfilePage';
import { Header, Footer } from '../components/Layout';

const IndexPage = () => {
  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);
  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const [currentDate, setCurrentDate] = useState(new Date());

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      if (currentScrollY > lastScrollY && currentScrollY > 100) {
        // Scrolling down and past 100px
        setIsVisible(false);
      } else if (currentScrollY < lastScrollY) {
        // Scrolling up
        setIsVisible(true);
      }
      
      setLastScrollY(currentScrollY);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);

  useEffect(() => {
    // Update date daily at midnight
    const updateDate = () => {
      setCurrentDate(new Date());
    };

    // Calculate milliseconds until next midnight
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);
    const msUntilMidnight = tomorrow.getTime() - now.getTime();

    // Set initial timeout for midnight, then interval for every 24 hours
    const initialTimeout = setTimeout(() => {
      updateDate();
      const dailyInterval = setInterval(updateDate, 24 * 60 * 60 * 1000);
      return () => clearInterval(dailyInterval);
    }, msUntilMidnight);

    return () => clearTimeout(initialTimeout);
  }, []);
  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'white' }}>
      {/* Header */}
      <Header 
        isVisible={isVisible} 
        onProfileClick={() => setProfileModalOpen(true)} 
      />


      {/* Main Content */}
      <Box
        sx={{
          flex: 1,
          pt: '120px',
          px: 4,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          maxWidth: '800px',
          mx: 'auto',
        }}
      >
        {/* Date & Category */}
        <Typography
          sx={{
            fontSize: '14px',
            color: '#666',
            mb: 3,
            textAlign: 'center',
          }}
        >
          {currentDate.toLocaleDateString('en-US', { 
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          })}
        </Typography>

        {/* Main Heading */}
        <Typography
          variant="h2"
          sx={{
            fontWeight: 700,
            fontSize: { xs: '32px', md: '48px' },
            color: '#000',
            textAlign: 'center',
            mb: 4,
            lineHeight: 1.2,
            fontFamily: 'Arial, Helvetica, sans-serif',
          }}
        >
{process.env.REACT_APP_TITLE}
        </Typography>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap', justifyContent: 'center' }}>
          <Button
            component={Link}
            to="/chat"
            variant="contained"
            sx={{
              backgroundColor: '#000',
              color: 'white',
              borderRadius: '20px',
              textTransform: 'none',
              px: 3,
              py: 1,
              fontSize: '16px',
              '&:hover': {
                backgroundColor: '#333',
              },
            }}
            endIcon={<ArrowUpward sx={{ transform: 'rotate(45deg)' }} />}
          >
            {process.env.REACT_APP_BUTTON_TRY}
          </Button>
          <Button
            component={Link}
            to="/home"
            sx={{
              color: '#666',
              textTransform: 'none',
              fontSize: '16px',
              '&:hover': {
                color: '#1976d2',
              },
            }}
            endIcon={<ArrowUpward sx={{ transform: 'rotate(45deg)' }} />}
          >
            {process.env.REACT_APP_BUTTON_TRY_WORK}
          </Button>
        </Box>

          
        {/* What is Base AI Builder */}
        <Box sx={{ maxWidth: '800px', textAlign: 'center', mb: 3, mt: 6 }}>
          <Typography
            variant="h3"
            sx={{
              fontWeight: 700,
              fontSize: { xs: '28px', md: '36px' },
              color: '#000',
              mb: 3,
              lineHeight: 1.2,
            }}
          >
            {process.env.REACT_APP_WHAT_IS_TITLE}
          </Typography>
          <Typography
            sx={{
              fontSize: '18px',
              lineHeight: 1.6,
              color: '#666',
              mb: 4,
              maxWidth: 660,
              mx: 'auto',
            }}
          >
            {process.env.REACT_APP_WHAT_IS_DESCRIPTION}
          </Typography>
        </Box>

        {/* AI Agents Section */}
        <Box sx={{ maxWidth: '800px', textAlign: 'center', mb: 6, mt: 3 }}>
          <Typography
            variant="h3"
            sx={{
              fontWeight: 700,
              fontSize: { xs: '28px', md: '36px' },
              color: '#000',
              mb: 3,
              lineHeight: 1.2,
            }}
          >
            {process.env.REACT_APP_AGENTS_TITLE}
          </Typography>
          <Typography
            sx={{
              fontSize: '18px',
              lineHeight: 1.6,
              color: '#666',
              mb: 4,
              maxWidth: 660,
              mx: 'auto',
            }}
          >
            {process.env.REACT_APP_AGENTS_DESCRIPTION}
          </Typography>
        </Box>

      </Box>

      {/* Footer */}
      <Footer />

      {/* Floating Ask Button */}
      <Box
        sx={{
          position: 'fixed',
          bottom: 30,
          left: '50%',
          transform: `translateX(-50%) ${isVisible ? 'translateY(0)' : 'translateY(100px)'}`,
          zIndex: 1000,
          opacity: isVisible ? 1 : 0,
          transition: 'all 0.3s ease-in-out',
        }}
      >
        <Button
          component={Link}
          to="/chat"
          variant="contained"
          sx={{
            backgroundColor: '#e0e0e0',
            color: '#666',
            borderRadius: '25px',
            textTransform: 'none',
            px: 3,
            py: 1.5,
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            '&:hover': {
              backgroundColor: '#d0d0d0',
            },
          }}
          endIcon={<ArrowUpward />}
        >
          {process.env.REACT_APP_BUTTON_ASK}
        </Button>
      </Box>
      
      {/* Profile Modal */}
      {profileModalOpen && (
        <ProfilePage 
          onClose={() => setProfileModalOpen(false)}
        />
      )}
    </Box>
  );
};

export default IndexPage;