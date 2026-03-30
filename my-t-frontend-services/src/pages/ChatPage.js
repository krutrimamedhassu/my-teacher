import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
    Box,
    IconButton,
    Typography,
    useTheme,
    useMediaQuery,
    CircularProgress
} from '@mui/material';
import {
    Menu as MenuIcon
} from '@mui/icons-material';
import LeftSidebar from '../components/Chat/LeftSidebar';
import RightSidebar from '../components/Chat/RightSidebar';
import MessageBubble from '../components/Chat/MessageBubble';
import TypingIndicator from '../components/Chat/TypingIndicator';
import ChatInput from '../components/Chat/ChatInput';

    import { 
    callResponderAPI, 
    uploadDocument, 
    
    createConversation,
    listConversations,
    listExampleConversations,
    getUserTier,
    getConversationById,
    sendMessageToConversation,
    editConversation,
        deleteConversation,
    getConversationSidebarInfo,
        deleteEmptyConversations,
        uploadMultipleDocuments,
        getConversationDocuments,
        deleteConversationDocument,
    validateFile
} from '../services';
import './ChatPage.css';
import { useParams, useNavigate } from 'react-router-dom';
import { v4 as uuidv4 } from 'uuid';
import { useSettings } from '../contexts/SettingsContext';
import { useAuth } from '../contexts/AuthContext';
import { useApiKey } from '../contexts/ApiKeyContext';
import ProfilePage from './ProfilePage';
import { WELCOME_MESSAGES, CHAT_TOOLS } from '../constants/chatConstants';
import { handleToolResponse } from '../utils/toolHandlers';

// Helper function to get file icons based on extension
const getFileIconFromExtension = (extension) => {
    switch (extension) {
        case 'pdf': return '📄';
        case 'docx':
        case 'doc': return '📝';
        case 'txt': return '📃';
        case 'html':
        case 'htm': return '🌐';
        default: return '📄';
    }
};

const ChatPage = () => {
    console.log('🔄 ChatPage: Component initialized');
    console.log('🧪 TEST LOG: If you see this, logging is working!');

    const { isAuthenticated: authContextIsAuthenticated, user: authUser, loading: authLoading } = useAuth();
    const { selectedApiKey } = useApiKey();
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [conversations, setConversations] = useState([]);
    const [exampleConversations, setExampleConversations] = useState([]);
    const [currentConversation, setCurrentConversation] = useState(null);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [userTier, setUserTier] = useState(null);
    const [isUserTierLoaded, setIsUserTierLoaded] = useState(false);
    const sidebarOpenTouchedRef = useRef(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);
    const [rightSidebarOpen, setRightSidebarOpen] = useState(false);
    const [qaPairs, setQaPairs] = useState(null);
    const [currentTool, setCurrentTool] = useState(CHAT_TOOLS.LEARNING_TOOLS);
    const [uploadedDocuments, setUploadedDocuments] = useState([]);
    const [conversationId, setConversationId] = useState(null);
    const [rightSidebarWidth, setRightSidebarWidth] = useState(840);
    const [isResizing, setIsResizing] = useState(false);
    const { conversationId: urlConversationId } = useParams();
    const navigate = useNavigate();
    const isExampleConversation = exampleConversations.some(e => e.id === urlConversationId)
        || (urlConversationId && urlConversationId.startsWith('00000000-0000-0000-'));
    const [sidebarInfoIndex, setSidebarInfoIndex] = useState(0);
    const [sidebarInfoList, setSidebarInfoList] = useState([]);
    const [streamingContent, setStreamingContent] = useState('');
    const bufferingIntervalRef = useRef(null);
    const [profileModalOpen, setProfileModalOpen] = useState(false);
    const [logoutHandled, setLogoutHandled] = useState(false);
    const [prevAuthState, setPrevAuthState] = useState(authContextIsAuthenticated);
    const [flashcards, setFlashcards] = useState(null);
    const [topicBreakdown, setTopicBreakdown] = useState(null);
    const [keyConcepts, setKeyConcepts] = useState(null);
    const [mcqSet, setMcqSet] = useState(null);
    const [studyPlan, setStudyPlan] = useState(null);
    const [visualData, setVisualData] = useState(null);
    const { settings } = useSettings();

    // Use welcome messages from constants
    const welcomeMessages = WELCOME_MESSAGES;
    const [currentWelcomeIndex, setCurrentWelcomeIndex] = useState(0);

    console.log('📱 ChatPage: isMobile =', isMobile);
    console.log('⚙️ ChatPage: Current settings:', settings);

    // Load example conversations once on mount (no auth required)
    useEffect(() => {
        listExampleConversations()
            .then(data => {
                if (Array.isArray(data)) {
                    setExampleConversations(data.map(c => ({
                        id: c.conversation_id,
                        title: c.title,
                        is_example: true
                    })));
                }
            })
            .catch(() => {});
    }, []);

    // Fetch authenticated user's tier (free/premium). Anonymous users: keep null.
    useEffect(() => {
        if (authLoading) return;
        if (!authContextIsAuthenticated) {
            setUserTier(null);
            setIsUserTierLoaded(true);
            return;
        }

        (async () => {
            try {
                const tierInfo = await getUserTier();
                setUserTier(tierInfo?.tier || null);
            } catch (e) {
                // Non-fatal: if tier fetch fails, default to non-premium behavior
                setUserTier(null);
            } finally {
                setIsUserTierLoaded(true);
            }
        })();
    }, [authLoading, authContextIsAuthenticated]);

    // Default left sidebar open for everyone except premium.
    useEffect(() => {
        if (authLoading) return;
        if (sidebarOpenTouchedRef.current) return;

        // Anonymous users: open immediately so they can see EXAMPLES.
        if (!authContextIsAuthenticated) {
            setSidebarOpen(true);
            return;
        }

        // Authenticated users: avoid flicker by waiting for tier to load.
        if (!isUserTierLoaded) return;

        const isPremium = userTier === 'premium';
        setSidebarOpen(!isPremium);
    }, [authLoading, authContextIsAuthenticated, isUserTierLoaded, userTier]);

    // Rotate welcome messages every 5 seconds when no messages
    useEffect(() => {
        if (messages.length === 0) {
            const interval = setInterval(() => {
                setCurrentWelcomeIndex((prevIndex) =>
                    (prevIndex + 1) % welcomeMessages.length
                );
            }, 5000);

            return () => clearInterval(interval);
        }
    }, [messages.length, welcomeMessages.length]);

    // Pre-fetch upload limits on component mount to avoid delays during upload
    useEffect(() => {
        const preloadUploadLimits = async () => {
            try {
                console.log('🔄 ChatPage: Pre-loading upload limits...');
                const { getUploadLimits } = await import('../services/fileUpload/fileValidation');
                await getUploadLimits();
                console.log('✅ ChatPage: Upload limits pre-loaded');
            } catch (error) {
                console.log('⚠️ ChatPage: Failed to pre-load upload limits:', error);
            }
        };
        
        preloadUploadLimits();
    }, []);

    console.log('🔗 ChatPage: urlConversationId =', urlConversationId);

    // Helper function to process messages consistently
    const processMessage = (msg) => {
        const sidebarInfo = msg.sidebar_info || {};
        return {
            id: msg.message_id || msg.id || Date.now(),
            content: msg.text || msg.content,
            sender: msg.role === 'assistant' ? 'ai' : 'user',
            timestamp: msg.timestamp || '',
            conversation_id: msg.conversation_id,
            attachments: msg.attachments || [],
            topicBreakdown: sidebarInfo.topicBreakdown || null,
            keyConcepts: sidebarInfo.keyConcepts || null,
            qaPairs: sidebarInfo.qaPairs || null,
            studyPlan: sidebarInfo.studyPlan || null,
            visualData: sidebarInfo.visualData || null,
            fileUpload: sidebarInfo.fileUpload || null,
            documentTool: sidebarInfo.documentTool || null,
            toolName: sidebarInfo.tool_name || null,
            sidebarOpened: sidebarInfo.sidebar_opened || null,
            sidebarContext: sidebarInfo.sidebar_context || null
        };
    };

    // Function to fetch all sidebar_info from the conversation
    const fetchSidebarInfo = async () => {
        if (!conversationId) return;

        try {
            const data = await getConversationSidebarInfo(conversationId);
            console.log('📱 ChatPage: Raw sidebar_info response:', data);

            // Sort by timestamp in descending order (latest first)
            const sortedList = (data.sidebar_info_list || []).sort((a, b) =>
                new Date(b.timestamp) - new Date(a.timestamp)
            );
            setSidebarInfoList(sortedList);
            setSidebarInfoIndex(0); // Start with the latest entry
            console.log('📱 ChatPage: Sorted sidebar_info list:', sortedList);

            // If we have entries, show the first (latest) one immediately
            if (sortedList.length > 0) {
                const latestInfo = sortedList[0];
                console.log('📱 ChatPage: Showing latest entry:', latestInfo);
                updateSidebarWithInfo(latestInfo.sidebar_info);
            }
        } catch (error) {
            console.error('📱 ChatPage: Error fetching sidebar_info:', error);
        }
    };

    // Helper function to clear all tool data except the specified one
    const clearOtherToolData = useCallback((keepTool) => {
        console.log('🧹 ChatPage: Clearing other tool data, keeping:', keepTool);
        
        if (keepTool !== 'flashcards') setFlashcards(null);
        if (keepTool !== 'topicBreakdown') setTopicBreakdown(null);
        if (keepTool !== 'keyConcepts') setKeyConcepts(null);
        if (keepTool !== 'mcqSet') setMcqSet(null);
        if (keepTool !== 'qaPairs') setQaPairs(null);
        if (keepTool !== 'studyPlan') setStudyPlan(null);
        if (keepTool !== 'visualData') setVisualData(null);
    }, []);

    // Function to update sidebar with sidebar_info
    const updateSidebarWithInfo = useCallback((info) => {
        if (!info) return;

        if (info.tool_name === 'generate_qa_pairs' && info.qaPairs) {
            clearOtherToolData('qaPairs');
            setQaPairs(info.qaPairs);
            setCurrentTool(CHAT_TOOLS.QA_PAIRS);
            if (settings.showRightSidebar !== false) {
                        setRightSidebarOpen(true);
                    }
        } else if (info.tool_name === 'generate_question_paper' && info.qaPairs) {
            clearOtherToolData('qaPairs');
            setQaPairs(info.qaPairs);
            setCurrentTool('Tools');
            if (settings.showRightSidebar !== false) {
                setRightSidebarOpen(true);
            }
        } else if (info.tool_name === 'generate_flashcards' && info.flashcards) {
            clearOtherToolData('flashcards');
            setFlashcards(info.flashcards);
            setCurrentTool('Tools');
            if (settings.showRightSidebar !== false) {
                setRightSidebarOpen(true);
            }
        } else if (info.tool_name === 'topic_breakdown' && info.topicBreakdown) {
            clearOtherToolData('topicBreakdown');
            setTopicBreakdown(info.topicBreakdown);
            setCurrentTool('Tools');
            if (settings.showRightSidebar !== false) {
                setRightSidebarOpen(true);
            }
        } else if (info.tool_name === 'extract_key_concepts' && info.keyConcepts) {
            clearOtherToolData('keyConcepts');
            setKeyConcepts(info.keyConcepts);
            setCurrentTool('Tools');
            if (settings.showRightSidebar !== false) {
                setRightSidebarOpen(true);
            }
        } else if (info.tool_name === 'generate_mcq_set' && info.mcqSet) {
            clearOtherToolData('mcqSet');
            setMcqSet(info.mcqSet);
            setCurrentTool('Tools');
            if (settings.showRightSidebar !== false) {
                setRightSidebarOpen(true);
            }
        } else if (info.tool_name === 'study_plan' && info.studyPlan) {
            clearOtherToolData('studyPlan');
            setStudyPlan(info.studyPlan);
            setCurrentTool('Tools');
            if (settings.showRightSidebar !== false) {
                setRightSidebarOpen(true);
            }
        } else if (info.tool_name === 'build_visual' && info.visualData) {
            clearOtherToolData('visualData');
            setVisualData(info.visualData);
            setCurrentTool('Tools');
            if (settings.showRightSidebar !== false) {
                setRightSidebarOpen(true);
            }
        }
    }, [settings.showRightSidebar, clearOtherToolData]);

    // Function to cycle through sidebar_info entries
    const cycleSidebarInfo = () => {
        if (sidebarInfoList.length === 0) {
            fetchSidebarInfo();
            return;
        }

        const nextIndex = (sidebarInfoIndex + 1) % sidebarInfoList.length;
        setSidebarInfoIndex(nextIndex);

        const currentInfo = sidebarInfoList[nextIndex];
        if (currentInfo && currentInfo.sidebar_info) {
            console.log('📱 ChatPage: Cycling to entry:', currentInfo);
            updateSidebarWithInfo(currentInfo.sidebar_info);
        }
    };

    const cycleSidebarInfoReverse = () => {
        if (sidebarInfoList.length === 0) {
            fetchSidebarInfo();
            return;
        }

        const prevIndex = (sidebarInfoIndex - 1 + sidebarInfoList.length) % sidebarInfoList.length;
        setSidebarInfoIndex(prevIndex);

        const currentInfo = sidebarInfoList[prevIndex];
        if (currentInfo && currentInfo.sidebar_info) {
            console.log('📱 ChatPage: Cycling backwards to entry:', currentInfo);
            updateSidebarWithInfo(currentInfo.sidebar_info);
        }
    };

    const scrollToBottom = () => {
        console.log('📜 ChatPage: scrollToBottom called');
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const handleMouseDown = (e) => {
        console.log('🖱️ ChatPage: handleMouseDown - Starting resize');
        setIsResizing(true);
        e.preventDefault();
    };

    const handleMouseMove = useCallback((e) => {
        if (!isResizing) return;

        const newWidth = window.innerWidth - e.clientX;
        const minWidth = 260;
        const maxWidth = 840;

        if (newWidth >= minWidth && newWidth <= maxWidth) {
            console.log('📏 ChatPage: handleMouseMove - Resizing sidebar to', newWidth, 'px');
            setRightSidebarWidth(newWidth);
        }
    }, [isResizing]);

    const handleMouseUp = useCallback(() => {
        console.log('🖱️ ChatPage: handleMouseUp - Stopping resize');
        setIsResizing(false);
    }, []);

    useEffect(() => {
        console.log('🖱️ ChatPage: useEffect - isResizing changed to', isResizing);
        if (isResizing) {
            console.log('🖱️ ChatPage: Adding mouse event listeners for resizing');
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);

            return () => {
                console.log('🖱️ ChatPage: Removing mouse event listeners');
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
            };
        }
    }, [isResizing, handleMouseMove, handleMouseUp]);

    // Handle window resize to adjust layout responsively
    useEffect(() => {
        const handleResize = () => {
            // Trigger re-render to recalculate widths
            setRightSidebarWidth(prevWidth => {
                const leftSidebarWidth = sidebarOpen ? 260 : 48;
                const minChatWidth = 300;
                const maxRightSidebarWidth = window.innerWidth - leftSidebarWidth - minChatWidth;
                return Math.min(prevWidth, Math.max(260, maxRightSidebarWidth));
            });
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [sidebarOpen]);


    const handleDeleteDocument = async (documentId) => {
        console.log('🗑️ ChatPage: handleDeleteDocument called with documentId =', documentId);
        if (!conversationId) {
            console.error('🗑️ ChatPage: No conversation ID available for document deletion');
            return;
        }
        
        try {
            console.log('🗑️ ChatPage: Calling deleteConversationDocument API...');
            console.log('🗑️ ChatPage: conversationId:', conversationId, 'documentId:', documentId);
            const response = await deleteConversationDocument(conversationId, documentId, true);
            console.log('🗑️ ChatPage: Document deleted successfully, response:', response);
            
            // Refresh documents from API to ensure sync with backend
            await fetchConversationDocuments(conversationId);
        } catch (error) {
            console.error('❌ ChatPage: Error deleting document:', error);
        }
    };

    useEffect(() => {
        console.log('📜 ChatPage: useEffect - messages or isTyping changed, scrolling to bottom');
        console.log('📜 ChatPage: messages count =', messages.length, 'isTyping =', isTyping);
        scrollToBottom();
    }, [messages, isTyping]);

    // On mount and when auth state changes, if no conversationId in URL, redirect to latest or check stored conversation
    useEffect(() => {
        // Don't run until auth loading is complete
        if (authLoading) {
            console.log('🚀 ChatPage: Skipping mount logic - auth still loading');
            return;
        }
        
        console.log('🚀 ChatPage: useEffect - Component mount/initialization');
        console.log('🚀 ChatPage: urlConversationId =', urlConversationId);
        console.log('🚀 ChatPage: authContextIsAuthenticated =', authContextIsAuthenticated);
        console.log('🚀 ChatPage: authLoading =', authLoading);
        console.log('🚀 ChatPage: authUser =', !!authUser);
        console.log('🚀 ChatPage: current path =', window.location.pathname);

        (async () => {
            // If no conversationId in URL, fetch user's most recent conversation
            if (!urlConversationId) {
                console.log('🚀 ChatPage: No URL conversation ID, fetching most recent conversation');
                
                let user;
                let userId;
                let username;
                
                if (authContextIsAuthenticated) {
                    user = authUser || JSON.parse(localStorage.getItem('user')) || {};
                    userId = user?.id;
                    username = user?.username;
                    console.log('🚀 ChatPage: Authenticated user - userId =', userId, 'username =', username);
                    
                    // Try to fetch user's most recent conversation
                    try {
                        const conversationsArr = await listConversations({ user_id: userId });
                        if (Array.isArray(conversationsArr) && conversationsArr.length > 0) {
                            // Get the most recent conversation (first in the list)
                            const mostRecentConversation = conversationsArr[0];
                            console.log('🚀 ChatPage: Found most recent conversation:', mostRecentConversation.conversation_id);
                            navigate(`/chat/${mostRecentConversation.conversation_id}`, { replace: true });
                            return;
                        }
                        console.log('🚀 ChatPage: No existing conversations found for authenticated user');
                    } catch (error) {
                        console.log('🚀 ChatPage: Error fetching conversations, will create new:', error);
                    }
                } else {
                    // For anonymous users: redirect to the welcome example conversation
                    const welcomeExampleId = '00000000-0000-0000-0000-000000000001';
                    console.log('🚀 ChatPage: Anonymous user, navigating to welcome example:', welcomeExampleId);
                    navigate(`/chat/${welcomeExampleId}`, { replace: true });
                    return;
                }

                // Generate ID locally and navigate immediately — don't wait on backend
                const newConversationId = uuidv4();
                console.log('🚀 ChatPage: Navigating immediately to new conversation:', newConversationId);
                navigate(`/chat/${newConversationId}`, { replace: true });
                // Register with backend in background
                try {
                    const response = await createConversation({ conversation_id: newConversationId, user_id: userId, username });
                    console.log('🚀 ChatPage: Conversation registered with backend:', response);
                    setConversations([{
                        id: newConversationId,
                        title: response?.conversation?.title || 'New Chat',
                        timestamp: response?.conversation?.created_at
                    }]);
                } catch (error) {
                    console.error('🚀 ChatPage: Failed to register conversation with backend:', error);
                }
            }
            // This logic is now handled above in the URL-first approach
        })();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [authContextIsAuthenticated, authLoading]);

    // When urlConversationId changes, fetch that conversation's messages
    useEffect(() => {
        if (urlConversationId) {
            setCurrentConversation(urlConversationId);
            setConversationId(urlConversationId);
            
            // Clear previous conversation's sidebar data before loading new conversation
            setFlashcards(null);
            setTopicBreakdown(null);
            setKeyConcepts(null);
            setMcqSet(null);
            setQaPairs(null);
            setStudyPlan(null);
            setVisualData(null);
            setSidebarInfoList([]);
            setSidebarInfoIndex(0);
            setCurrentTool(CHAT_TOOLS.LEARNING_TOOLS);
            
            (async () => {
                try {
                    const conv = await getConversationById(urlConversationId);
                    if (conv && Array.isArray(conv.messages)) {
                        // When parsing messages from backend, extract tool data from the sidebar_info object:
                        const processedMessages = conv.messages.map(processMessage);
                        setMessages(processedMessages);

                        // Fetch documents for this conversation immediately
                        await fetchConversationDocuments(urlConversationId);

                        // Fetch sidebar_info and check if last message used a sidebar tool
                        try {
                            const sidebarData = await getConversationSidebarInfo(urlConversationId);
                            console.log('📱 ChatPage: Fetched sidebar_info on load:', sidebarData);

                            if (sidebarData.sidebar_info_list && sidebarData.sidebar_info_list.length > 0) {
                                // Sort by timestamp in descending order (latest first)
                                const sortedList = sidebarData.sidebar_info_list.sort((a, b) =>
                                    new Date(b.timestamp) - new Date(a.timestamp)
                                );
                                setSidebarInfoList(sortedList);
                                setSidebarInfoIndex(0);

                                // Get the latest sidebar_info entry
                                const latestInfo = sortedList[0];
                                console.log('📱 ChatPage: Latest sidebar_info:', latestInfo);

                                // Define tools that should open the sidebar
                                const SIDEBAR_TOOLS = [
                                    'generate_qa_pairs',
                                    'generate_question_paper',
                                    'generate_flashcards',
                                    'topic_breakdown',
                                    'extract_key_concepts',
                                    'generate_mcq_set',
                                    'study_plan',
                                    'build_visual'
                                ];

                                // Get the last message's tool name (only from the last message, no fallback)
                                const lastMessage = processedMessages[processedMessages.length - 1];
                                const lastMessageToolName = lastMessage?.toolName;

                                console.log('📱 ChatPage: Last message tool:', lastMessageToolName);
                                console.log('📱 ChatPage: Last message:', lastMessage);

                                // Only auto-open sidebar if the last message used a sidebar tool
                                if (lastMessageToolName && SIDEBAR_TOOLS.includes(lastMessageToolName)) {
                                    console.log('📱 ChatPage: Last message used sidebar tool, auto-opening sidebar');
                                    updateSidebarWithInfo(latestInfo.sidebar_info);
                                } else {
                                    console.log('📱 ChatPage: Last message did NOT use sidebar tool, keeping sidebar closed');
                                    setRightSidebarOpen(false);
                                }
                            } else {
                                // No sidebar_info found, keep sidebar closed
                                console.log('📱 ChatPage: No sidebar_info found, keeping sidebar closed');
                                setRightSidebarOpen(false);
                            }
                        } catch (sidebarError) {
                            console.error('📱 ChatPage: Error fetching sidebar_info:', sidebarError);
                            setRightSidebarOpen(false);
                        }

                        // Update title in conversations list
                        setConversations(prev => prev.map(c =>
                            c.id === conv.conversation_id ? { ...c, title: conv.title } : c
                        ));
                    } else {
                        setMessages([]);
                        setUploadedDocuments([]);
                        setCurrentTool(CHAT_TOOLS.LEARNING_TOOLS);
                        setRightSidebarOpen(false);
                    }
                } catch (error) {
                    setMessages([]);
                    setUploadedDocuments([]);
                    setCurrentTool(CHAT_TOOLS.LEARNING_TOOLS);
                    setRightSidebarOpen(false);
                }
            })();
            
            // Auto-focus the chat input after page load/conversation load
            setTimeout(() => {
                if (inputRef.current) {
                    // For Material-UI TextField, need to focus the actual input element
                    const inputElement = inputRef.current.querySelector('input') || 
                                       inputRef.current.querySelector('textarea') ||
                                       inputRef.current;
                    if (inputElement && typeof inputElement.focus === 'function') {
                        inputElement.focus();
                    }
                }
            }, 300);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [urlConversationId, updateSidebarWithInfo]);

    // Load conversations list when authenticated and on chat page
    useEffect(() => {
        if (authContextIsAuthenticated && authUser) {
            (async () => {
                try {
                    const user = authUser || JSON.parse(localStorage.getItem('user')) || {};
                    const conversationsArr = await listConversations({ user_id: user?.id });
                    if (Array.isArray(conversationsArr)) {
                        setConversations(conversationsArr.map(conv => ({
                            id: conv.conversation_id,
                            title: conv.title,
                            timestamp: conv.created_at,
                            last_message_preview: conv.last_message_preview,
                            is_active: conv.is_active
                        })));
                    }
                } catch (error) {
                    console.error('Failed to load conversations:', error);
                }
            })();
        }
    }, [authContextIsAuthenticated, authUser]);

    // Clear anonymous conversation state when user logs in (auth changes from false to true)
    useEffect(() => {
        console.log('🔐 ChatPage: Auth state change detected:', {
            prevAuthState,
            authContextIsAuthenticated,
            authUser: !!authUser,
            currentPath: window.location.pathname,
            conversationId,
            messagesCount: messages.length
        });
        
        // If auth state changed from false to true (user just logged in)
        if (!prevAuthState && authContextIsAuthenticated && authUser) {
            console.log('🔐 ChatPage: LOGIN DETECTED - User just logged in, clearing anonymous conversation state');
            console.log('🔐 ChatPage: Before clearing - messages:', messages.length, 'conversationId:', conversationId);
            
            // Clear all existing state to start fresh for authenticated user
            setMessages([]);
            setConversations([]);
            setCurrentConversation(null);
            setConversationId(null);
            setUploadedDocuments([]);
            
            // Clear all right sidebar state
            setQaPairs(null);
            setFlashcards(null);
            setTopicBreakdown(null);
            setKeyConcepts(null);
            setMcqSet(null);
            setStudyPlan(null);
            setVisualData(null);
            setCurrentTool(CHAT_TOOLS.LEARNING_TOOLS);
            setRightSidebarOpen(false);
            setSidebarInfoList([]);
            setSidebarInfoIndex(0);
            setStreamingContent('');
            
            console.log('🔐 ChatPage: State cleared, forcing navigation to /chat');
            
            // Force redirect to /chat to trigger fresh authenticated conversation loading
            if (window.location.pathname.startsWith('/chat/')) {
                navigate('/chat', { replace: true });
            }
        }
        
        setPrevAuthState(authContextIsAuthenticated);
    }, [authContextIsAuthenticated, authUser, prevAuthState, navigate, conversationId, messages.length]);

    // Auto-clean empty conversations on page load/refresh for authenticated users
    useEffect(() => {
        (async () => {
            if (!authContextIsAuthenticated || !authUser) return;
            try {
                await deleteEmptyConversations();
                const user = authUser || JSON.parse(localStorage.getItem('user')) || {};
                const conversationsArr = await listConversations({ user_id: user?.id });
                if (Array.isArray(conversationsArr)) {
                    setConversations(conversationsArr.map(conv => ({
                        id: conv.conversation_id,
                        title: conv.title,
                        timestamp: conv.created_at,
                        last_message_preview: conv.last_message_preview,
                        is_active: conv.is_active
                    })));
                }
            } catch (error) {
                // Non-fatal: if cleanup fails, silently continue
                console.warn('Cleanup of empty conversations skipped:', error?.message || error);
            }
        })();
    }, [authContextIsAuthenticated, authUser]);

    // Clear authenticated user's chat data when user logs out, but allow anonymous access
    useEffect(() => {
        if (!authContextIsAuthenticated && !authLoading && authUser === null && !logoutHandled) {
            console.log('🚪 ChatPage: User logged out, clearing authenticated chat data');
            setLogoutHandled(true); // Prevent multiple executions
            
            // Clear conversations and user-specific data, but allow anonymous usage
            setConversations([]);
            setCurrentConversation(null);
            setConversationId(null);
            setUploadedDocuments([]);
            setMessages([]);
            
            // Clear ALL right sidebar state
            setQaPairs(null);
            setFlashcards(null);
            setTopicBreakdown(null);
            setKeyConcepts(null);
            setMcqSet(null);
            setStudyPlan(null);
            setVisualData(null);
            setCurrentTool(CHAT_TOOLS.LEARNING_TOOLS);
            setRightSidebarOpen(false);
            setSidebarInfoList([]);
            setSidebarInfoIndex(0);
            setStreamingContent('');
            
            // Create exactly ONE new anonymous conversation
            (async () => {
                try {
                    let anonUserId = localStorage.getItem('anon_user_id');
                    if (!anonUserId) {
                        anonUserId = uuidv4();
                        localStorage.setItem('anon_user_id', anonUserId);
                    }
                    
                    console.log('🚪 ChatPage: Creating ONE new anonymous conversation');
                    const response = await createConversation({ 
                        user_id: anonUserId, 
                        username: 'anonymous' 
                    });
                    
                    console.log('🚪 ChatPage: Anonymous conversation created:', response.conversation_id);
                    
                    // Navigate directly to the new conversation
                    navigate(`/chat/${response.conversation_id}`, { replace: true });
                } catch (error) {
                    console.error('🚪 ChatPage: Failed to create anonymous conversation:', error);
                }
            })();
        }
        
        // Reset the flag when user logs back in
        if (authContextIsAuthenticated && logoutHandled) {
            setLogoutHandled(false);
        }
    }, [authContextIsAuthenticated, authLoading, authUser, logoutHandled, navigate]);

    // Function to fetch documents from conversation documents endpoint
    const fetchConversationDocuments = useCallback(async (conversation_id) => {
        if (!conversation_id) return;
        
        try {
            console.log('📚 ChatPage: Fetching documents for conversation:', conversation_id);
            const response = await getConversationDocuments(conversation_id);
            console.log('📚 ChatPage: Documents response:', response);
            
            if (response && response.documents && Array.isArray(response.documents)) {
                const formattedDocuments = response.documents.map(doc => ({
                    id: doc.document_id || doc.id,
                    name: doc.filename || doc.file_name || doc.name,
                    size: doc.file_size || doc.size,
                    type: doc.file_type || doc.mime_type || doc.type,
                    uploadTime: doc.added_at || doc.upload_date || doc.created_at || new Date().toISOString(),
                    ...doc // Keep any additional properties
                }));
                setUploadedDocuments(formattedDocuments);
                console.log('📚 ChatPage: Set documents from API:', formattedDocuments.length);
            } else {
                console.log('📚 ChatPage: No documents found in API response');
                setUploadedDocuments([]);
            }
        } catch (error) {
            console.error('📚 ChatPage: Error fetching conversation documents:', error);
            // Fall back to extracting from messages if API fails
            console.log('📚 ChatPage: Falling back to message-based document extraction');
            
            const documentMessages = messages.filter(msg =>
                (msg.fileUpload && msg.fileUpload.status === 'success') ||
                (msg.attachments && msg.attachments.length > 0)
            );
            if (documentMessages.length > 0) {
                const restoredDocuments = [];
                documentMessages.forEach(msg => {
                    // Handle old fileUpload format
                    if (msg.fileUpload && msg.fileUpload.status === 'success') {
                        restoredDocuments.push({
                            id: msg.fileUpload.documentId || Date.now().toString(),
                            name: msg.fileUpload.fileName,
                            size: msg.fileUpload.fileSize,
                            type: msg.fileUpload.fileType,
                            uploadTime: msg.fileUpload.uploadTime || new Date().toISOString(),
                        });
                    }
                    // Handle new attachments format
                    if (msg.attachments && msg.attachments.length > 0) {
                        msg.attachments.forEach(attachment => {
                            if (attachment.type === 'document') {
                                restoredDocuments.push({
                                    id: attachment.document_id,
                                    name: attachment.filename,
                                    size: attachment.filesize,
                                    type: attachment.file_type,
                                    uploadTime: new Date().toISOString(),
                                });
                            }
                        });
                    }
                });
                setUploadedDocuments(restoredDocuments);
                console.log('📚 ChatPage: Restored documents from messages:', restoredDocuments.length);
            } else {
                setUploadedDocuments([]);
                console.log('📚 ChatPage: No documents found in messages either');
            }
        }
    }, [messages]);

    // Fallback function to restore sidebar from message parsing (old logic)
    const restoreSidebarFromMessages = useCallback(async (processedMessages) => {

        // Restore QA pairs from messages if they exist
        const qaMessage = processedMessages.find(msg =>
            msg.qaPairs && msg.qaPairs.qa_pairs
        );
        if (qaMessage) {
            setQaPairs(qaMessage.qaPairs);
            setCurrentTool('QA Pairs');
            if (settings.showRightSidebar !== false) {
                        setRightSidebarOpen(true);
                    }
        } else {
            setQaPairs(null);
        }

        // Only set default state if no special tools are active
        if (!qaMessage) {
            setCurrentTool(CHAT_TOOLS.LEARNING_TOOLS);
            setRightSidebarOpen(false);
        }

        // Try to fetch documents from the API endpoint first
        await fetchConversationDocuments(conversationId);
        
        // If API fetch failed or no documents, fall back to extracting from messages
        // (this logic will be in the fetchConversationDocuments function's catch block)
    }, [settings.showRightSidebar, conversationId, fetchConversationDocuments]);

    const handleFileUpload = async (files, messageText = '', visualDisplayData = null) => {
        // Handle both single file and array of files
        const fileArray = Array.isArray(files) ? files : [files];
        console.log('📁 ChatPage: handleFileUpload called with files:', {
            count: fileArray.length,
            files: fileArray.map(f => ({ name: f.name, size: f.size, type: f.type })),
            hasVisualDisplayData: !!visualDisplayData,
            visualDisplayData: visualDisplayData
        });

        // Show immediate feedback on right side of chat rail
        const uploadStartMessage = {
            id: Date.now() + '_upload_start',
            content: `📤 Preparing to upload ${fileArray.length} file${fileArray.length > 1 ? 's' : ''}...`,
            sender: 'user', // This makes it appear on the right side
            timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, uploadStartMessage]);

        // Enforce maximum of 8 files
        if (fileArray.length > 8) {
            const errorMessage = {
                id: Date.now(),
                content: `❌ You can upload up to 8 documents at a time. You selected ${fileArray.length}.`,
                sender: 'ai',
                timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, errorMessage]);
            return;
        }

        // Validate all files in parallel for better performance
        console.log('🔍 ChatPage: Starting file validation...');
        const validationPromises = fileArray.map(file => validateFile(file));
        const validationResults = await Promise.all(validationPromises);
        
        // Check for validation errors
        for (let i = 0; i < fileArray.length; i++) {
            const file = fileArray[i];
            const validation = validationResults[i];
            
            if (!validation.isValid) {
                console.log('❌ ChatPage: File validation failed:', validation.errors);
                const errorMessage = {
                    id: Date.now(),
                    content: `❌ ${file.name}: ${validation.errors.join(' ')}`,
                    sender: 'ai',
                    timestamp: new Date().toLocaleTimeString()
                };
                setMessages(prev => [...prev, errorMessage]);
                return;
            }
        }
        console.log('✅ ChatPage: All files validated successfully');

        // First, show user's message if they typed something
        if (messageText.trim()) {
            let user_id;
            let username;

            if (authContextIsAuthenticated) {
                const user = authUser || JSON.parse(localStorage.getItem('user')) || {};
                user_id = user?.id;
                username = user?.username;
            } else {
                user_id = localStorage.getItem('anon_user_id');
                if (!user_id) {
                    user_id = uuidv4();
                    localStorage.setItem('anon_user_id', user_id);
                }
                username = 'anonymous';
            }

            const userTextMessage = {
                sender_id: user_id,
                sender_username: username,
                role: 'user',
                text: messageText.trim(),
                attachments: []
            };

            // Add user message to UI immediately
            const tempUserMessage = {
                id: Date.now() + '_temp_user',
                content: messageText.trim(),
                sender: 'user',
                timestamp: new Date().toISOString(),
                conversation_id: conversationId
            };
            setMessages(prevMessages => [...prevMessages, tempUserMessage]);
            
            // Persist user message to backend
            await sendMessageToConversation(conversationId, userTextMessage);
        }

        // No progress message - just show typing indicator

        setIsTyping(true);

        // Upload results aggregation
        const uploadResults = [];
        const newDocuments = [];

        try {
            if (fileArray.length === 1) {
                // Single file: use single-upload endpoint
                const file = fileArray[0];
                console.log(`📁 ChatPage: Uploading single file: ${file.name}`);
                try {
                    const response = await uploadDocument(file, conversationId);
                    console.log(`📁 ChatPage: Upload response for ${file.name}:`, response);
                    if (response && response.document_id) {
                        uploadResults.push({ file, response, success: true });
                        newDocuments.push({
                            id: response.document_id,
                            name: file.name,
                            size: file.size,
                            type: file.type,
                            uploadTime: new Date().toISOString(),
                            ...response
                        });
                    } else {
                        uploadResults.push({
                            file,
                            response,
                            success: false,
                            error: response?.error || 'Upload failed - no document ID returned'
                        });
                    }
                } catch (fileError) {
                    console.error(`📁 ChatPage: Failed to upload ${file.name}:`, fileError);
                    uploadResults.push({ file, response: null, success: false, error: fileError.message });
                }
            } else {
                // Multiple files: use multi-upload endpoint
                console.log(`📁 ChatPage: Uploading ${fileArray.length} files via multi-upload endpoint`);
                const multiResponse = await uploadMultipleDocuments(fileArray, conversationId);
                console.log('📁 ChatPage: Multi-upload response:', multiResponse);

                // Try to extract uploaded items array from various possible shapes
                let items = Array.isArray(multiResponse)
                    ? multiResponse
                    : (multiResponse?.uploads || multiResponse?.uploaded || multiResponse?.documents || multiResponse?.data || multiResponse?.results || []);

                if (!Array.isArray(items)) items = [];

                // Build a map from filename to returned metadata when possible
                const returnedByName = new Map();
                items.forEach((it) => {
                    const name = it?.filename || it?.file_name || it?.name || it?.original_filename || it?.originalName || it?.metadata?.original_filename;
                    if (name) returnedByName.set(name, it);
                });

                // Merge client File info with server response
                const usedIndexes = new Set();
                for (let i = 0; i < fileArray.length; i++) {
                    const file = fileArray[i];
                    let serverItem = returnedByName.get(file.name) || null;
                    if (!serverItem && items.length === fileArray.length) {
                        // Fallback by index if counts match
                        for (let idx = 0; idx < items.length; idx++) {
                            if (!usedIndexes.has(idx)) {
                                serverItem = items[idx];
                                usedIndexes.add(idx);
                                break;
                            }
                        }
                    }
                    const documentId = serverItem?.document_id || serverItem?.id || serverItem?.documentId || null;
                    if (documentId) {
                        const merged = {
                            document_id: documentId,
                            filename: serverItem?.file_name || serverItem?.filename || serverItem?.metadata?.original_filename || file.name,
                            filesize: serverItem?.file_info?.file_size || serverItem?.filesize || serverItem?.size || file.size,
                            file_type: serverItem?.file_info?.mime_type || serverItem?.file_type || serverItem?.type || file.type
                        };
                        uploadResults.push({ file, response: merged, success: true });
                        newDocuments.push({
                            id: merged.document_id,
                            name: merged.filename,
                            size: merged.filesize,
                            type: merged.file_type,
                            uploadTime: new Date().toISOString(),
                            ...merged
                        });
                    } else {
                        uploadResults.push({ file, response: serverItem, success: false, error: 'Upload failed - no document ID returned' });
                    }
                }
            }

            // Update uploaded documents list
            setUploadedDocuments(prev => [...prev, ...newDocuments]);

            // Separate successful and failed uploads
            const successfulUploads = uploadResults.filter(r => r.success);
            const failedUploads = uploadResults.filter(r => !r.success);

            // Get user info for the document upload message
            let user_id;
            let username;

            if (authContextIsAuthenticated) {
                const user = authUser || JSON.parse(localStorage.getItem('user')) || {};
                user_id = user?.id;
                username = user?.username;
            } else {
                user_id = localStorage.getItem('anon_user_id');
                if (!user_id) {
                    user_id = uuidv4();
                    localStorage.setItem('anon_user_id', user_id);
                }
                username = 'anonymous';
            }

            // Show user message with documents
            if (successfulUploads.length > 0) {
                const documentMessage = {
                    sender_id: user_id,
                    sender_username: username,
                    role: 'user',
                    text: ``,
                    attachments: successfulUploads.map(r => ({
                        type: 'document',
                        document_id: r.response.document_id,
                        filename: r.response.filename || r.file.name,
                        filesize: r.response.filesize || r.file.size,
                        file_type: r.response.file_type || r.file.type
                    })),
                    // Include visual display data for consistent rendering
                    visual_display_data: visualDisplayData || successfulUploads.map(r => ({
                        id: Date.now() + Math.random(),
                        displayName: (r.response.filename || r.file.name).replace(/\.[^/.]+$/, ""),
                        extension: (r.response.filename || r.file.name).split('.').pop().toLowerCase(),
                        fileType: r.response.file_type || r.file.type,
                        fileIcon: getFileIconFromExtension((r.response.filename || r.file.name).split('.').pop().toLowerCase()),
                        timestamp: new Date().toISOString(),
                        originalFileName: r.file.name,
                        fileSize: r.response.filesize || r.file.size
                    }))
                };

                console.log('📊 ChatPage: Sending document message with visual display data:', {
                    attachmentsCount: documentMessage.attachments.length,
                    hasVisualData: !!documentMessage.visual_display_data,
                    visualDataCount: documentMessage.visual_display_data?.length || 0
                });

                // Persist user document message to backend
                await sendMessageToConversation(conversationId, documentMessage);

                // Add simple confirmation message with filenames
                const fileNames = successfulUploads.map(r => r.file.name);
                const fileNamesText = fileNames.length === 1 
                    ? fileNames[0] 
                    : fileNames.join(', ');
                
                const confirmationMessage = {
                    sender_id: null,
                    sender_username: 'assistant',
                    role: 'assistant',
                    text: `✅ Successfully uploaded ${successfulUploads.length === 1 ? 'document' : `${successfulUploads.length} documents`}: ${fileNamesText}`,
                    attachments: []
                };

                // Persist confirmation message to backend
                await sendMessageToConversation(conversationId, confirmationMessage);
            }

            // Handle failed uploads with AI message if any failed
            if (failedUploads.length > 0) {
                const failedNames = failedUploads.map(r => `${r.file.name} (${r.error})`).join(', ');
                const errorMessage = {
                    sender_id: null,
                    sender_username: 'assistant',
                    role: 'assistant',
                    text: `❌ Failed to upload ${failedUploads.length} files: ${failedNames}`,
                    attachments: []
                };
                
                // Persist error message to backend
                await sendMessageToConversation(conversationId, errorMessage);
            }

            // Fetch updated messages from backend to ensure consistency
            const conv = await getConversationById(conversationId);
            if (conv && Array.isArray(conv.messages)) {
                const processedMessages = conv.messages.map(processMessage);
                setMessages(processedMessages);
                await restoreSidebarFromMessages(processedMessages);
            }

            // Refresh documents list to show newly uploaded files
            await fetchConversationDocuments(conversationId);

            // Remove the upload start message
            setMessages(prev => prev.filter(msg => msg.id !== uploadStartMessage.id));

        } catch (error) {
            // Remove the upload start message on error too
            setMessages(prev => prev.filter(msg => msg.id !== uploadStartMessage.id));
            console.error('Error uploading files:', error);

            let errorContent;
            
            if (error.isSessionExpired || (error.status === 401 && authContextIsAuthenticated)) {
                // Session expired for authenticated user
                errorContent = 'Your session has expired. Please login again to continue.\n\n[Login](/login)';
            } else if (!authContextIsAuthenticated && (error.status === 401 || error.status === 403)) {
                // User is not authenticated and needs to login
                errorContent = 'I see that you are an unauthenticated user. Please login to upload files.\n\n[Login](/login) | [Sign Up](/register)';
            } else if (error.isLimitError || (authContextIsAuthenticated && (error.status === 429 || error.message?.includes('limit')))) {
                // Special handling for authenticated users who have exceeded their plan limits
                errorContent = 'I see you have completed enough uploads. Please upgrade your plan to upload more files.\n\n[Upgrade Plan](/pricing)';
            } else {
                // Default error message for other errors
                const fileNames = fileArray.map(f => f.name).join(', ');
                errorContent = `❌ Failed to upload files: ${fileNames}. Error: ${error.message}`;
            }

            const errorMessage = {
                id: Date.now() + 1,
                content: errorContent,
                sender: 'ai',
                timestamp: new Date().toLocaleTimeString(),
                isLimitError: error.isLimitError || (error.status === 429)
            };
            setMessages(prev => [...prev, errorMessage]);

            // Persist error message to backend
            const backendErrorMessage = {
                sender_id: null,
                sender_username: 'assistant',
                role: 'assistant',
                text: errorContent,
                attachments: []
            };

            try {
                await sendMessageToConversation(conversationId, backendErrorMessage);
                // Fetch updated messages from backend
                const conv = await getConversationById(conversationId);
                if (conv && Array.isArray(conv.messages)) {
                    const processedMessages = conv.messages.map(processMessage);
                    setMessages(processedMessages);
                    await restoreSidebarFromMessages(processedMessages);
                }
            } catch (persistError) {
                console.error('Failed to persist error message to backend:', persistError);
            }
        } finally {
            setIsTyping(false);
        }
    };

    const handleSendMessage = async () => {
        console.log('💬 ChatPage: handleSendMessage called');
        console.log('💬 ChatPage: inputValue =', inputValue);

        if (isExampleConversation) {
            console.log('💬 ChatPage: Read-only example conversation, blocking message send');
            return;
        }

        if (!inputValue.trim()) {
            console.log('💬 ChatPage: Empty input, returning early');
            return;
        }

        // Prepare user message for backend
        let user_id;
        let username;

        if (authContextIsAuthenticated) {
            const user = authUser || JSON.parse(localStorage.getItem('user')) || {};
            user_id = user?.id;
            username = user?.username;
            console.log('💬 ChatPage: Authenticated user - userId =', user_id, 'username =', username);
        } else {
            // For anonymous users, get or generate anonymous user ID
            user_id = localStorage.getItem('anon_user_id');
            if (!user_id) {
                user_id = uuidv4();
                localStorage.setItem('anon_user_id', user_id);
                console.log('💬 ChatPage: Generated new anonymous userId for message =', user_id);
            } else {
                console.log('💬 ChatPage: Using existing anonymous userId for message =', user_id);
            }
            username = 'anonymous';
        }

        const userMessage = {
            sender_id: user_id,
            sender_username: username,
            role: 'user',
            text: inputValue,
            attachments: []
        };
        console.log('💬 ChatPage: Prepared user message =', userMessage);

        // Add user message to UI immediately for instant feedback
        const tempUserMessage = {
            id: Date.now() + '_temp',
            content: inputValue,
            sender: 'user',
            timestamp: new Date().toISOString(),
            conversation_id: conversationId
        };
        console.log('💬 ChatPage: Adding user message immediately to UI');
        setMessages(prevMessages => [...prevMessages, tempUserMessage]);
        
        // Scroll to bottom immediately to show the user's message
        setTimeout(() => scrollToBottom(), 10);

        console.log('💬 ChatPage: Setting isTyping to true');
        setIsTyping(true);
        setStreamingContent('');
        console.log('💬 ChatPage: Clearing input value');
        setInputValue('');

        try {
            // If no conversation exists yet (e.g. createConversation failed on load), create one now
            let activeConversationId = conversationId;
            if (!activeConversationId) {
                const anonUserId = localStorage.getItem('anon_user_id') || user_id;
                const newConv = await createConversation({ user_id: anonUserId, username });
                activeConversationId = newConv.conversation_id;
                setConversationId(activeConversationId);
                setCurrentConversation(activeConversationId);
                navigate(`/chat/${activeConversationId}`, { replace: true });
            }

            // Persist user message to backend
            await sendMessageToConversation(activeConversationId, userMessage);
            // Fetch updated messages from backend to sync with server
            const conv = await getConversationById(activeConversationId);
            if (conv && Array.isArray(conv.messages)) {
                const processedMessages = conv.messages.map(processMessage);
                setMessages(processedMessages);
                await restoreSidebarFromMessages(processedMessages);
            }

            // Call the API (supports streaming UI mode)
            const statusLabels = ['understanding', 'brewing', 'cooking', 'boozing', 'thinking', 'crafting'];
            let labelIndex = 0;
            if (settings.streamingMode === 'streaming') {
                setStreamingContent(`${statusLabels[labelIndex]}...`);
                if (bufferingIntervalRef.current) {
                    clearInterval(bufferingIntervalRef.current);
                }
                bufferingIntervalRef.current = setInterval(() => {
                    labelIndex = (labelIndex + 1) % statusLabels.length;
                    setStreamingContent(`${statusLabels[labelIndex]}...`);
                }, 700);
            }

            console.log('💬 ChatPage: Calling responder API');
            const response = await callResponderAPI(userMessage.text, activeConversationId, selectedApiKey);

            if (settings.streamingMode === 'streaming' && bufferingIntervalRef.current) {
                clearInterval(bufferingIntervalRef.current);
                bufferingIntervalRef.current = null;
            }
            if (settings.streamingMode === 'streaming') {
                setStreamingContent('');
            }
            // Handle tool responses using our organized tool handlers
            const toolResult = await handleToolResponse(response, {
                conversationId,
                settings,
                setStreamingContent,
                setMessages,
                setQaPairs,
                setFlashcards,
                setTopicBreakdown,
                setKeyConcepts,
                setMcqSet,
                setStudyPlan,
                setVisualData,
                setCurrentTool,
                setRightSidebarOpen
            });
            
            if (toolResult.handled) {
                // Tool was handled by our tool handlers
                if (toolResult.messages) {
                    setMessages(toolResult.messages);
                }
            } else {
                // Fallback: tool not recognized, handle as regular message
                const aiMessage = {
                    sender_id: null,
                    sender_username: 'assistant',
                    role: 'assistant',
                    text: response.response,
                    attachments: []
                };
                await sendMessageToConversation(activeConversationId, aiMessage);

                // Fetch updated messages from backend
                const convAfterAI = await getConversationById(activeConversationId);
                if (convAfterAI && Array.isArray(convAfterAI.messages)) {
                    const processedMessages = convAfterAI.messages.map(msg => {
                                        return {
                            id: msg.message_id || msg.id || Date.now(),
                            content: msg.text || msg.content,
                            sender: msg.role === 'assistant' ? 'ai' : 'user',
                            timestamp: msg.timestamp || '',
                            conversation_id: msg.conversation_id,
                            fileUpload: msg.sidebar_info?.fileUpload || null,
                        };
                    });
                    setMessages(processedMessages);
                    
                    // Update title in conversations list
                    setConversations(prev => prev.map(c =>
                        c.id === convAfterAI.conversation_id ? { ...c, title: convAfterAI.title } : c
                    ));
                }
            }
            
            // Only close sidebar if not QA pairs, visual tool, flashcards, topic breakdown, question paper, key concepts, MCQ set, or study plan
            if (response.tool !== 'generate_qa_pairs' && 
                response.tool !== 'generate_question_paper' && 
                response.tool !== 'build_visual' && 
                response.tool !== 'generate_flashcards' && 
                response.tool !== 'topic_breakdown' && 
                response.tool !== 'extract_key_concepts' && 
                response.tool !== 'generate_mcq_set' && 
                response.tool !== 'study_plan') {
                setRightSidebarOpen(false);
                setCurrentTool(CHAT_TOOLS.LEARNING_TOOLS);
            }
            
            // This replaces all the old tool handling code below
        } catch (error) {
            console.error('Error sending message:', error);
            
            let errorContent;
            let shouldRemoveUserMessage = false;
            
            if (error.isSessionExpired || (error.status === 401 && authContextIsAuthenticated)) {
                // Session expired for authenticated user
                errorContent = 'Your session has expired. Please login again to continue.\n\n[Login](/login)';
                shouldRemoveUserMessage = true;
            } else if (!authContextIsAuthenticated && (error.status === 401 || error.status === 403)) {
                // User is not authenticated and needs to login
                errorContent = 'I see that you are an unauthenticated user. Please login to ask more questions.\n\n[Login](/login) | [Sign Up](/register)';
                shouldRemoveUserMessage = true;
            } else if (error.isLimitError || (authContextIsAuthenticated && (error.status === 429 || error.message?.includes('limit')))) {
                // Special handling for authenticated users who have exceeded their plan limits
                errorContent = 'I see you have completed enough questions. Please upgrade your plan to ask more questions.\n\n[Upgrade Plan](/pricing)';
                shouldRemoveUserMessage = true;
            } else if (error.status === 404 && !authContextIsAuthenticated) {
                // For logged-out users getting 404, assume it's an authentication issue
                errorContent = 'I see that you are an unauthenticated user. Please login to ask more questions.\n\n[Login](/login) | [Sign Up](/register)';
                shouldRemoveUserMessage = true;
            } else {
                errorContent = 'I apologize, but I\'m having trouble processing your request right now. Please try again in a moment.';
            }
            
            // Remove the temporary user message for auth/limit errors
            if (shouldRemoveUserMessage) {
                setMessages(prev => prev.filter(msg => msg.id !== tempUserMessage.id));
            }
            
            const errorMessage = {
                id: Date.now() + 1,
                content: errorContent,
                sender: 'ai',
                timestamp: new Date().toLocaleTimeString(),
                isLimitError: error.isLimitError || (error.status === 404 && !authContextIsAuthenticated)
            };
            setMessages(prev => [...prev, errorMessage]);
            setRightSidebarOpen(false);
        } finally {
            if (bufferingIntervalRef.current) {
                clearInterval(bufferingIntervalRef.current);
                bufferingIntervalRef.current = null;
            }
            setIsTyping(false);
            // Auto-focus the chat input after AI response
            setTimeout(() => {
                if (inputRef.current) {
                    // For Material-UI TextField, need to focus the actual input element
                    const inputElement = inputRef.current.querySelector('input') || 
                                       inputRef.current.querySelector('textarea') ||
                                       inputRef.current;
                    if (inputElement && typeof inputElement.focus === 'function') {
                        inputElement.focus();
                    }
                }
            }, 100);
        }
    };

    const handleKeyPress = (e) => {
        console.log('⌨️ ChatPage: handleKeyPress - key =', e.key, 'shiftKey =', e.shiftKey);
        if (e.key === 'Enter' && !e.shiftKey) {
            console.log('⌨️ ChatPage: Enter pressed without shift, sending message');
            e.preventDefault();
            handleSendMessage();
        }
    };

    const createNewConversation = async () => {
        console.log('🆕 ChatPage: createNewConversation called');
        // Generate ID and navigate immediately
        const newConversationId = uuidv4();
        navigate(`/chat/${newConversationId}`);
        setConversationId(newConversationId);
        setCurrentConversation(newConversationId);
        try {
            let user = null;
            if (authContextIsAuthenticated) {
                user = authUser || JSON.parse(localStorage.getItem('user')) || {};
                console.log('🆕 ChatPage: Authenticated user =', user);
            } else {
                console.log('🆕 ChatPage: No authenticated user');
            }
            console.log('🆕 ChatPage: Registering conversation with user_id =', user?.id, 'username =', user?.username);
            const response = await createConversation({
                conversation_id: newConversationId,
                user_id: user?.id,
                username: user?.username
            });
            // Refresh conversations list
            if (authContextIsAuthenticated) {
                const conversationsArr = await listConversations({ user_id: user?.id });
                if (Array.isArray(conversationsArr)) {
                    setConversations(conversationsArr.map(conv => ({
                        id: conv.conversation_id,
                        title: conv.title,
                        timestamp: conv.created_at,
                        last_message_preview: conv.last_message_preview,
                        is_active: conv.is_active
                    })));
                }
            } else {
                setConversations(prev => [
                    {
                        id: response.conversation_id,
                        title: response.conversation.title,
                        timestamp: response.conversation.created_at
                    },
                    ...prev.filter(c => c.id !== response.conversation_id)
                ]);
            }
            // Always navigate to the new conversation
            navigate(`/chat/${response.conversation_id}`);
            // Fetch messages for the new conversation
            try {
                const conv = await getConversationById(response.conversation_id);
                if (conv && Array.isArray(conv.messages)) {
                    const processedMessages = conv.messages.map(msg => {
                                        return {
                            id: msg.message_id || msg.id || Date.now(),
                            content: msg.text || msg.content,
                            sender: msg.role === 'assistant' ? 'ai' : 'user',
                            timestamp: msg.timestamp || '',
                            conversation_id: msg.conversation_id,
                                topicBreakdown: msg.sidebar_info?.topicBreakdown || null,
                            keyConcepts: msg.sidebar_info?.keyConcepts || null,
                            qaPairs: msg.sidebar_info?.qaPairs || null,
                            visualFlowchart: msg.sidebar_info?.visualFlowchart || null,
                            visualConceptMap: msg.sidebar_info?.visualConceptMap || null,
                            fileUpload: msg.sidebar_info?.fileUpload || null,
                            documentTool: msg.sidebar_info?.documentTool || null,
                            toolName: msg.sidebar_info?.tool_name || null
                        };
                    });
                    setMessages(processedMessages);




                    // Restore QA pairs from messages if they exist
                    const qaMessage = processedMessages.find(msg =>
                        msg.qaPairs && msg.qaPairs.qa_pairs
                    );
                    if (qaMessage) {
                        setQaPairs(qaMessage.qaPairs);
                        setCurrentTool(CHAT_TOOLS.QA_PAIRS);
                        if (settings.showRightSidebar !== false) {
                        setRightSidebarOpen(true);
                    }
                    } else {
                        setQaPairs(null);
                    }

                    // Only set default state if no special tools are active
                    if (!qaMessage) {
                        setCurrentTool(CHAT_TOOLS.LEARNING_TOOLS);
                        setRightSidebarOpen(false);
                    }

                    // Restore uploaded documents from messages if they exist
                    const documentMessages = processedMessages.filter(msg =>
                        msg.fileUpload && msg.fileUpload.status === 'success'
                    );
                    if (documentMessages.length > 0) {
                        const restoredDocuments = documentMessages.map(msg => ({
                            id: msg.fileUpload.documentId || Date.now().toString(),
                            name: msg.fileUpload.fileName,
                            size: msg.fileUpload.fileSize,
                            type: msg.fileUpload.fileType,
                            uploadTime: msg.fileUpload.uploadTime || new Date().toISOString(),
                        }));
                        setUploadedDocuments(restoredDocuments);
                    } else {
                        setUploadedDocuments([]);
                    }
                } else {
                    setMessages([]);
                    setUploadedDocuments([]);
                    setCurrentTool(CHAT_TOOLS.LEARNING_TOOLS);
                    setRightSidebarOpen(false);
                }
            } catch (error) {
                setMessages([]);
                // setFlashcards([]); // REMOVED
                setUploadedDocuments([]);
                setCurrentTool(CHAT_TOOLS.LEARNING_TOOLS);
                setRightSidebarOpen(false);
            }
        } catch (error) {
            console.error('Failed to create conversation:', error);
        }
    };

    const handleEditConversation = async (conversationId, newTitle) => {
        console.log('✏️ ChatPage: handleEditConversation called with conversationId =', conversationId, 'newTitle =', newTitle);
        if (exampleConversations.some(e => e.id === conversationId)) return;
        try {
            console.log('✏️ ChatPage: Calling editConversation API...');
            const updated = await editConversation(conversationId, { title: newTitle });
            console.log('✏️ ChatPage: Conversation updated successfully:', updated);
            setConversations(prev => {
                const updatedList = prev.map(c => c.id === conversationId ? { ...c, title: updated.title } : c);
                console.log('✏️ ChatPage: Updated conversations list, new count:', updatedList.length);
                return updatedList;
            });
        } catch (error) {
            console.error('❌ ChatPage: Failed to rename conversation:', error);
            alert('Failed to rename conversation.');
        }
    };
    const handleDeleteConversation = async (conversationId) => {
        console.log('🗑️ ChatPage: handleDeleteConversation called with conversationId =', conversationId);
        console.log('🗑️ ChatPage: currentConversation =', currentConversation);
        if (exampleConversations.some(e => e.id === conversationId)) return;
        try {
            console.log('🗑️ ChatPage: Calling deleteConversation API...');
            await deleteConversation(conversationId);
            console.log('🗑️ ChatPage: Conversation deleted successfully');
            setConversations(prev => {
                const filtered = prev.filter(c => c.id !== conversationId);
                console.log('🗑️ ChatPage: Updated conversations list, new count:', filtered.length);
                return filtered;
            });
            // If the deleted conversation is current, redirect to /chat
            if (conversationId === currentConversation) {
                console.log('🗑️ ChatPage: Deleted conversation was current, navigating to /chat');
                navigate('/chat');
            }
        } catch (error) {
            console.error('❌ ChatPage: Failed to delete conversation:', error);
            alert('Failed to delete conversation.');
        }
    };


    // Show loading spinner only while auth is loading
    if (authLoading) {
        return (
            <Box
                sx={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    minHeight: '100vh',
                    background: '#f8f8f8',
                }}
            >
                <CircularProgress size={60} />
            </Box>
        );
    }

    return (
        <Box sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            display: 'flex',
            bgcolor: 'white',
            filter: profileModalOpen ? 'blur(1px)' : 'none',
            transition: 'filter 0.3s ease-in-out',
            overflow: 'hidden'
        }}>
            {/* Left Sidebar - always rendered, shrinks when closed */}
            <LeftSidebar
                conversations={conversations}
                exampleConversations={exampleConversations}
                currentConversation={currentConversation}
                setCurrentConversation={setCurrentConversation}
                createNewConversation={createNewConversation}
                theme={theme}
                open={sidebarOpen}
                onClose={() => {
                    sidebarOpenTouchedRef.current = true;
                    setSidebarOpen(false);
                }}
                onOpen={() => {
                    sidebarOpenTouchedRef.current = true;
                    setSidebarOpen(true);
                }}
                onSelectConversation={id => navigate(`/chat/${id}`)}
                onEditConversation={handleEditConversation}
                onDeleteConversation={handleDeleteConversation}
                 onProfileClick={() => setProfileModalOpen(true)}
            />

            {/* Main Chat Area */}
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    height: '100vh',
                    position: 'relative',
                    bgcolor: 'white',
                    flex: 1,
                    minWidth: '300px',
                    overflow: 'hidden'
                }}
            >
                <div className="chat-rail">
                    {/* Mobile Menu Button */}
                    {isMobile && (
                        <Box
                            sx={{
                                position: 'fixed',
                                top: 16,
                                left: 16,
                                zIndex: theme.zIndex.drawer + 1
                            }}
                        >
                            <IconButton
                                onClick={() => {
                                    console.log('📱 ChatPage: Mobile menu button clicked, current sidebarOpen =', sidebarOpen);
                                    sidebarOpenTouchedRef.current = true;
                                    setSidebarOpen(!sidebarOpen);
                                }}
                                sx={{
                                    bgcolor: 'background.paper',
                                    boxShadow: 2,
                                    '&:hover': {
                                        bgcolor: 'background.paper'
                                    }
                                }}
                            >
                                <MenuIcon />
                            </IconButton>
                        </Box>
                    )}

                    {/* Desktop Left Sidebar Open Button */}
                    {/* Removed: now handled by Sidebar's own minimal state */}

                    {/* Messages Area - REMOVE messages-container wrapper */}
                    {messages.length === 0 ? (
                        <Box
                            sx={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                justifyContent: 'center',
                                textAlign: 'center',
                                px: 3,
                                width: '100%',
                                height: '100vh',
                                minHeight: 0,
                                wordBreak: 'break-word',
                                maxWidth: 500,
                                margin: '0 auto',
                                position: 'relative'
                            }}
                        >
                            <Typography variant="h4" color="black" gutterBottom sx={{
                                transition: 'opacity 0.3s ease-in-out, transform 0.3s ease-in-out',
                                minHeight: '48px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                position: 'absolute',
                                top: '50%',
                                left: '50%',
                                transform: 'translate(-50%, -70px)',
                                width: '100%',
                                fontFamily: 'sans-serif',
                                fontWeight: 320 // Make text thin/light
                            }}>
                                {welcomeMessages[currentWelcomeIndex]}
                            </Typography>

                            {/* Quick action buttons */}
                            <Box sx={{
                                position: 'absolute',
                                top: '50%',
                                left: '50%',
                                transform: 'translate(-50%, 70px)', // Move buttons up a little
                                display: 'flex',
                                flexDirection: 'column',
                                gap: 1,
                                justifyContent: 'center',
                                width: '100%', // Full width of parent
                                minWidth: '700px', // Force minimum 700px
                                maxWidth: '1200px', // Allow up to 1200px
                                height: '150px'
                            }}>
                                {/* Responsive buttons that wrap based on available width */}
                            </Box>
                        </Box>
                    ) : (
                        <Box
                            sx={{
                                width: '100%',
                                maxWidth: 'min(778px, calc(100% - 32px))',
                                margin: '0 auto',
                                px: '10px'
                            }}
                        >
                            {messages.map((message) => (
                                <MessageBubble key={message.id} message={message} theme={theme} />
                            ))}
                            {isTyping && <TypingIndicator theme={theme} streamingContent={streamingContent} isStreaming={settings.streamingMode === 'streaming'} />}
                        </Box>
                    )}
                    <div ref={messagesEndRef} />
                </div>



                {/* Input Area - moved outside chat-rail for proper fixed positioning */}
                <ChatInput
                    inputValue={inputValue}
                    setInputValue={setInputValue}
                    handleSendMessage={handleSendMessage}
                    handleKeyPress={handleKeyPress}
                    isTyping={isTyping}
                    inputRef={inputRef}
                    theme={theme}
                    isMobile={isMobile}
                    onFileUpload={handleFileUpload}
                    hasMessages={messages.length > 0}
                    onFilesAttachedChange={() => {}}
                    isReadOnly={isExampleConversation}
                />
            </Box>

            {/* Right Sidebar - conditionally rendered based on settings */}
            {settings.showRightSidebar !== false && (
                <RightSidebar
                    theme={theme}
                    open={rightSidebarOpen}
                    currentTool={currentTool}
                    qaPairs={qaPairs}
                    flashcards={flashcards}
                    topicBreakdown={topicBreakdown}
                    keyConcepts={keyConcepts}
                    mcqSet={mcqSet}
                    studyPlan={studyPlan}
                    visualData={visualData}
                    uploadedDocuments={uploadedDocuments}
                    rightSidebarWidth={rightSidebarWidth}
                    isMobile={isMobile}
                    isResizing={isResizing}
                    onClose={() => setRightSidebarOpen(false)}
                    onToggleOpen={(tool) => {
                        if (tool) {
                            setCurrentTool(tool);
                        }
                        if (settings.showRightSidebar !== false) {
                        setRightSidebarOpen(true);
                    }
                    }}
                    onDeleteDocument={handleDeleteDocument}
                    onCycleSidebarInfo={cycleSidebarInfo}
                    onCycleSidebarInfoReverse={cycleSidebarInfoReverse}
                    onMouseDown={handleMouseDown}
                    onProfileClick={() => setProfileModalOpen(true)}
                />
            )}

            {/* Profile Modal */}
            {profileModalOpen && (
                <ProfilePage
                    onClose={() => setProfileModalOpen(false)}
                />
            )}
        </Box>
    );
};

export default ChatPage; 