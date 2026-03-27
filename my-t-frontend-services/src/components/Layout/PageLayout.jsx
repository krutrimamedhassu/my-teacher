import React, { useState, useEffect } from 'react';
import { Box } from '@mui/material';
import Header from './Header';
import Footer from './Footer';
import ProfilePage from '../../pages/ProfilePage';

const PageLayout = ({ children, showHeader = true, showFooter = true, showFloatingButton = false }) => {
  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);
  const [profileModalOpen, setProfileModalOpen] = useState(false);

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

    if (showHeader) {
      window.addEventListener('scroll', handleScroll);
      return () => window.removeEventListener('scroll', handleScroll);
    }
  }, [lastScrollY, showHeader]);

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'white' }}>
      {/* Header */}
      {showHeader && (
        <Header 
          isVisible={isVisible} 
          onProfileClick={() => setProfileModalOpen(true)} 
        />
      )}

      {/* Main Content */}
      <Box sx={{ flex: 1, pt: showHeader ? '60px' : 0 }}>
        {children}
      </Box>

      {/* Footer */}
      {showFooter && <Footer />}

      {/* Profile Modal */}
      {profileModalOpen && (
        <ProfilePage 
          onClose={() => setProfileModalOpen(false)}
        />
      )}
    </Box>
  );
};

export default PageLayout;