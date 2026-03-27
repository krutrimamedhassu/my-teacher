// ExplorePage.js

import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Typography,
    useTheme,
    useMediaQuery
} from '@mui/material';
import LeftSidebar from '../components/Chat/LeftSidebar';
import RightSidebar from '../components/Chat/RightSidebar';
import { useAuth } from '../contexts/AuthContext';
import { listConversations } from '../services';
import ProfilePage from './ProfilePage';


export default function ExplorePage() {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));
    const navigate = useNavigate();
    const { isAuthenticated, user } = useAuth();
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [rightSidebarOpen, setRightSidebarOpen] = useState(false);
    const [rightSidebarWidth, setRightSidebarWidth] = useState(840);
    const [isResizing, setIsResizing] = useState(false);
    const [profileModalOpen, setProfileModalOpen] = useState(false);
    const [conversations, setConversations] = useState([]);

    const handleMouseDown = (e) => {
        setIsResizing(true);
        e.preventDefault();
    };
    const handleMouseMove = useCallback((e) => {
        if (!isResizing) return;
        const newWidth = window.innerWidth - e.clientX;
        const minWidth = 260;
        const maxWidth = 840;
        if (newWidth >= minWidth && newWidth <= maxWidth) {
            setRightSidebarWidth(newWidth);
        }
    }, [isResizing]);
    const handleMouseUp = useCallback(() => {
        setIsResizing(false);
    }, []);

    React.useEffect(() => {
        if (isResizing) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            return () => {
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
            };
        }
    }, [isResizing, handleMouseMove, handleMouseUp]);

    // Load conversations for the left sidebar when authenticated
    React.useEffect(() => {
        const loadConversations = async () => {
            try {
                if (!isAuthenticated || !user?.id) {
                    setConversations([]);
                    return;
                }
                const conversationsArr = await listConversations({ user_id: user.id });
                if (Array.isArray(conversationsArr)) {
                    setConversations(conversationsArr.map(conv => ({
                        id: conv.conversation_id,
                        title: conv.title,
                        timestamp: conv.created_at,
                        last_message_preview: conv.last_message_preview || ''
                    })));
                } else {
                    setConversations([]);
                }
            } catch (err) {
                setConversations([]);
            }
        };
        loadConversations();
    }, [isAuthenticated, user]);

    return (
        <>
        <Box sx={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', display: 'flex', bgcolor: 'white', overflow: 'hidden', filter: profileModalOpen ? 'blur(1px)' : 'none', transition: 'filter 0.3s ease-in-out' }}>
            {/* Left Sidebar */}
            <LeftSidebar
                conversations={conversations}
                currentConversation={null}
                setCurrentConversation={() => {}}
                createNewConversation={() => navigate('/chat')}
                theme={theme}
                open={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
                onOpen={() => setSidebarOpen(true)}
                onSelectConversation={(id) => navigate(`/chat/${id}`)}
                onEditConversation={(id) => navigate(`/chat/${id}`)}
                onDeleteConversation={() => navigate('/chat')}
                onProfileClick={() => setProfileModalOpen(true)}
            />

            {/* Main Explore Content */}
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    height: '100vh',
                    position: 'relative',
                    bgcolor: 'white',
                    width: (() => {
                        if (isMobile) return '100%';
                        const leftSidebarWidth = sidebarOpen ? 260 : 48;
                        const rightSidebarWidthCalc = rightSidebarOpen ? (rightSidebarWidth || 840) : 48;
                        const totalSidebarWidth = leftSidebarWidth + rightSidebarWidthCalc;
                        const availableWidth = window.innerWidth - totalSidebarWidth;
                        const minWidth = 300;
                        return `${Math.max(availableWidth, minWidth)}px`;
                    })(),
                    minWidth: '300px',
                    transition: 'width 0.3s ease',
                    px: 4,
                    py: 6,
                    background: theme.palette.background.default
                }}
            >
                <Box sx={{ textAlign: 'center', mb: 5 }}>
                    <Typography variant="h4" component="h1" gutterBottom>
                        Explore More
                    </Typography>
                </Box>
            </Box>

            {/* Right Sidebar */}
            <RightSidebar
                theme={theme}
                open={rightSidebarOpen}
                currentTool={'Learning Tools'}
                qaPairs={null}
                uploadedDocuments={[]}
                rightSidebarWidth={rightSidebarWidth}
                isMobile={isMobile}
                isResizing={isResizing}
                onClose={() => setRightSidebarOpen(false)}
                onToggleOpen={() => setRightSidebarOpen(true)}
                onDeleteDocument={() => {}}
                onCycleSidebarInfo={() => {}}
                onMouseDown={handleMouseDown}
                onProfileClick={() => setProfileModalOpen(true)}
            />
        </Box>
        {profileModalOpen && (
            <ProfilePage onClose={() => setProfileModalOpen(false)} />
        )}
        </>
    );
}