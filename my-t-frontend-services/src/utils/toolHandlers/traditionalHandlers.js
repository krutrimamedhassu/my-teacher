/**
 * TRADITIONAL MODE TOOL HANDLERS
 * Handles tools with instant display, sidebar interactions, and standard responses
 */

import { sendMessageToConversation, getConversationById } from '../../services';

/**
 * Helper function to clear all tool data except the specified one
 * This ensures only one tool's content is shown at a time
 */
const clearOtherToolData = (keepTool, params) => {
    const {
        setFlashcards,
        setTopicBreakdown,
        setKeyConcepts,
        setMcqSet,
        setQaPairs,
        setStudyPlan,
        setVisualData
    } = params;
    
    console.log('🧹 Clearing other tool data, keeping:', keepTool);
    
    if (keepTool !== 'flashcards') setFlashcards(null);
    if (keepTool !== 'topicBreakdown') setTopicBreakdown(null);
    if (keepTool !== 'keyConcepts') setKeyConcepts(null);
    if (keepTool !== 'mcqSet') setMcqSet(null);
    if (keepTool !== 'qaPairs') setQaPairs(null);
    if (keepTool !== 'studyPlan') setStudyPlan(null);
    if (keepTool !== 'visualData') setVisualData(null);
};

/**
 * Handle bramha tool without streaming (instant display)
 */
export const handleBramhaTraditional = async (response, conversationId) => {
    const aiMessage = {
        sender_id: null,
        sender_username: 'assistant',
        role: 'assistant',
        text: response.response,
        attachments: []
    };
    await sendMessageToConversation(conversationId, aiMessage);
    
    // Fetch updated messages from backend
    const convAfterAI = await getConversationById(conversationId);
    if (convAfterAI && Array.isArray(convAfterAI.messages)) {
        const processedMessages = convAfterAI.messages.map(msg => {
            const sidebarInfo = msg.sidebar_info || {};
            return {
                id: msg.message_id || msg.id || Date.now(),
                content: msg.text || msg.content,
                sender: msg.role === 'assistant' ? 'ai' : 'user',
                timestamp: msg.timestamp || '',
                conversation_id: msg.conversation_id,
                fileUpload: sidebarInfo.fileUpload || null,
            };
        });
        return { messages: processedMessages, handled: true };
    }
    return { handled: true };
};

/**
 * Handle generate_flashcards tool - display flashcards in right sidebar
 */
export const handleFlashcardsTraditional = async (response, conversationId, params) => {
    const { setFlashcards, setCurrentTool, setRightSidebarOpen, settings } = params;
    
    console.log('🎯 Flashcards tool handler called with response:', response);
    console.log('🎯 Settings:', settings);
    console.log('🎯 Available params:', Object.keys(params));
    
    // Parse the flashcard response data
    let flashcardsData = null;
    try {
        if (typeof response.response === 'string') {
            flashcardsData = JSON.parse(response.response);
        } else {
            flashcardsData = response.response;
        }
        console.log('🎯 Parsed flashcards data:', flashcardsData);
    } catch (error) {
        console.error('Failed to parse flashcards response:', error);
        return { handled: false };
    }
    
    if (flashcardsData && flashcardsData.flashcards) {
        console.log('🎯 Found flashcards, setting state...');
        // Clear other tool data first, then set flashcards
        clearOtherToolData('flashcards', params);
        setFlashcards(flashcardsData);
        setCurrentTool('Tools');
        console.log('🎯 showRightSidebar setting:', settings.showRightSidebar);
        if (settings.showRightSidebar !== false) {
            console.log('🎯 Opening right sidebar...');
            setRightSidebarOpen(true);
        } else {
            console.log('🎯 Right sidebar disabled in settings');
        }
        
        // Send confirmation message
        const confirmationText = `✨ Generated ${flashcardsData.flashcards.length} Flashcards on ${flashcardsData.subject_area} (${flashcardsData.difficulty_level} level). Look in the Right Sidebar to view them.`;
        const aiMessage = {
            sender_id: null,
            sender_username: 'assistant',
            role: 'assistant',
            text: confirmationText,
            attachments: [],
            sidebar_info: {
                tool_name: 'generate_flashcards',
                flashcards: flashcardsData,
                sidebar_opened: true,
                sidebar_context: 'flashcards'
            }
        };
        await sendMessageToConversation(conversationId, aiMessage);
        
        // Fetch updated messages from backend
        const convAfterAI = await getConversationById(conversationId);
        if (convAfterAI && Array.isArray(convAfterAI.messages)) {
            const processedMessages = convAfterAI.messages.map(msg => {
                const sidebarInfo = msg.sidebar_info || {};
                return {
                    id: msg.message_id || msg.id || Date.now(),
                    content: msg.text || msg.content,
                    sender: msg.role === 'assistant' ? 'ai' : 'user',
                    timestamp: msg.timestamp || '',
                    conversation_id: msg.conversation_id,
                    flashcards: sidebarInfo.flashcards || null,
                    fileUpload: sidebarInfo.fileUpload || null,
                };
            });
            return { messages: processedMessages, handled: true };
        }
    }
    
    return { handled: true };
};

/**
 * Handle topic_breakdown tool - display topic breakdown in right sidebar
 */
export const handleTopicBreakdownTraditional = async (response, conversationId, params) => {
    const { setTopicBreakdown, setCurrentTool, setRightSidebarOpen, settings } = params;
    
    console.log('📚 Topic breakdown tool handler called with response:', response);
    console.log('📚 Settings:', settings);
    console.log('📚 Available params:', Object.keys(params));
    
    // Parse the topic breakdown response data
    let breakdownData = null;
    try {
        if (typeof response.response === 'string') {
            breakdownData = JSON.parse(response.response);
        } else {
            breakdownData = response.response;
        }
        console.log('📚 Parsed topic breakdown data:', breakdownData);
    } catch (error) {
        console.error('Failed to parse topic breakdown response:', error);
        return { handled: false };
    }
    
    if (breakdownData && breakdownData.topics) {
        console.log('📚 Found topic breakdown, setting state...');
        // Clear other tool data first, then set topic breakdown
        clearOtherToolData('topicBreakdown', params);
        setTopicBreakdown(breakdownData);
        setCurrentTool('Tools');
        console.log('📚 showRightSidebar setting:', settings.showRightSidebar);
        if (settings.showRightSidebar !== false) {
            console.log('📚 Opening right sidebar...');
            setRightSidebarOpen(true);
        } else {
            console.log('📚 Right sidebar disabled in settings');
        }
        
        // Send confirmation message
        const confirmationText = `📚 Generated topic breakdown for ${breakdownData.subject_area} with ${breakdownData.topics.length} topics. Check it out in the sidebar!`;
        const aiMessage = {
            sender_id: null,
            sender_username: 'assistant',
            role: 'assistant',
            text: confirmationText,
            attachments: [],
            sidebar_info: {
                tool_name: 'topic_breakdown',
                topicBreakdown: breakdownData,
                sidebar_opened: true,
                sidebar_context: 'topic_breakdown'
            }
        };
        await sendMessageToConversation(conversationId, aiMessage);
        
        // Fetch updated messages from backend
        const convAfterAI = await getConversationById(conversationId);
        if (convAfterAI && Array.isArray(convAfterAI.messages)) {
            const processedMessages = convAfterAI.messages.map(msg => {
                const sidebarInfo = msg.sidebar_info || {};
                return {
                    id: msg.message_id || msg.id || Date.now(),
                    content: msg.text || msg.content,
                    sender: msg.role === 'assistant' ? 'ai' : 'user',
                    timestamp: msg.timestamp || '',
                    conversation_id: msg.conversation_id,
                    flashcards: sidebarInfo.flashcards || null,
                    topicBreakdown: sidebarInfo.topicBreakdown || null,
                    fileUpload: sidebarInfo.fileUpload || null,
                };
            });
            return { messages: processedMessages, handled: true };
        }
    }
    
    return { handled: true };
};

/**
 * Handle extract_key_concepts tool - display key concepts in right sidebar
 */
export const handleKeyConceptsTraditional = async (response, conversationId, params) => {
    const { setKeyConcepts, setCurrentTool, setRightSidebarOpen, settings } = params;
    
    console.log('🔑 Key concepts tool handler called with response:', response);
    console.log('🔑 Settings:', settings);
    console.log('🔑 Available params:', Object.keys(params));
    console.log('🔑 setKeyConcepts function:', typeof setKeyConcepts);
    console.log('🔑 setRightSidebarOpen function:', typeof setRightSidebarOpen);
    
    // Parse the key concepts response data
    let conceptsData = null;
    try {
        if (typeof response.response === 'string') {
            conceptsData = JSON.parse(response.response);
        } else {
            conceptsData = response.response;
        }
        console.log('🔑 Parsed key concepts data:', conceptsData);
    } catch (error) {
        console.error('Failed to parse key concepts response:', error);
        return { handled: false };
    }
    
    if (conceptsData && conceptsData.concepts) {
        console.log('🔑 Found key concepts, setting state...');
        // Clear other tool data first, then set key concepts
        clearOtherToolData('keyConcepts', params);
        setKeyConcepts(conceptsData);
        setCurrentTool('Tools');
        console.log('🔑 showRightSidebar setting:', settings.showRightSidebar);
        if (settings.showRightSidebar !== false) {
            console.log('🔑 Opening right sidebar...');
            setRightSidebarOpen(true);
        } else {
            console.log('🔑 Right sidebar disabled in settings');
        }
        
        // Send confirmation message
        const confirmationText = `🔑 Extracted ${conceptsData.concepts.length} key concepts for ${conceptsData.subject_area}. Check them out in the sidebar!`;
        const aiMessage = {
            sender_id: null,
            sender_username: 'assistant',
            role: 'assistant',
            text: confirmationText,
            attachments: [],
            sidebar_info: {
                tool_name: 'extract_key_concepts',
                keyConcepts: conceptsData,
                sidebar_opened: true,
                sidebar_context: 'key_concepts'
            }
        };
        await sendMessageToConversation(conversationId, aiMessage);
        
        // Fetch updated messages from backend
        const convAfterAI = await getConversationById(conversationId);
        if (convAfterAI && Array.isArray(convAfterAI.messages)) {
            const processedMessages = convAfterAI.messages.map(msg => {
                const sidebarInfo = msg.sidebar_info || {};
                return {
                    id: msg.message_id || msg.id || Date.now(),
                    content: msg.text || msg.content,
                    sender: msg.role === 'assistant' ? 'ai' : 'user',
                    timestamp: msg.timestamp || '',
                    conversation_id: msg.conversation_id,
                    flashcards: sidebarInfo.flashcards || null,
                    topicBreakdown: sidebarInfo.topicBreakdown || null,
                    keyConcepts: sidebarInfo.keyConcepts || null,
                    fileUpload: sidebarInfo.fileUpload || null,
                };
            });
            return { messages: processedMessages, handled: true };
        }
    }
    
    return { handled: true };
};

/**
 * Handle generate_mcq_set tool - display MCQs in right sidebar
 */
export const handleMCQSetTraditional = async (response, conversationId, params) => {
    const { setMcqSet, setCurrentTool, setRightSidebarOpen, settings } = params;
    
    console.log('📝 MCQ set tool handler called with response:', response);
    console.log('📝 Settings:', settings);
    console.log('📝 Available params:', Object.keys(params));
    console.log('📝 setMcqSet function:', typeof setMcqSet);
    console.log('📝 setRightSidebarOpen function:', typeof setRightSidebarOpen);
    
    // Parse the MCQ set response data
    let mcqData = null;
    try {
        if (typeof response.response === 'string') {
            mcqData = JSON.parse(response.response);
        } else {
            mcqData = response.response;
        }
        console.log('📝 Parsed MCQ data:', mcqData);
    } catch (error) {
        console.error('Failed to parse MCQ set response:', error);
        return { handled: false };
    }
    
    if (mcqData && mcqData.mcqs) {
        console.log('📝 Found MCQ set, setting state...');
        // Clear other tool data first, then set MCQ set
        clearOtherToolData('mcqSet', params);
        setMcqSet(mcqData);
        setCurrentTool('Tools');
        console.log('📝 showRightSidebar setting:', settings.showRightSidebar);
        if (settings.showRightSidebar !== false) {
            console.log('📝 Opening right sidebar...');
            setRightSidebarOpen(true);
        } else {
            console.log('📝 Right sidebar disabled in settings');
        }
        
        // Send confirmation message
        const confirmationText = `📝 Generated ${mcqData.mcqs.length} multiple choice questions on ${mcqData.subject_area} (${mcqData.difficulty_level} level). Test your knowledge in the sidebar!`;
        const aiMessage = {
            sender_id: null,
            sender_username: 'assistant',
            role: 'assistant',
            text: confirmationText,
            attachments: [],
            sidebar_info: {
                tool_name: 'generate_mcq_set',
                mcqSet: mcqData,
                sidebar_opened: true,
                sidebar_context: 'mcq_set'
            }
        };
        await sendMessageToConversation(conversationId, aiMessage);
        
        // Fetch updated messages from backend
        const convAfterAI = await getConversationById(conversationId);
        if (convAfterAI && Array.isArray(convAfterAI.messages)) {
            const processedMessages = convAfterAI.messages.map(msg => {
                const sidebarInfo = msg.sidebar_info || {};
                return {
                    id: msg.message_id || msg.id || Date.now(),
                    content: msg.text || msg.content,
                    sender: msg.role === 'assistant' ? 'ai' : 'user',
                    timestamp: msg.timestamp || '',
                    conversation_id: msg.conversation_id,
                    flashcards: sidebarInfo.flashcards || null,
                    topicBreakdown: sidebarInfo.topicBreakdown || null,
                    keyConcepts: sidebarInfo.keyConcepts || null,
                    mcqSet: sidebarInfo.mcqSet || null,
                    fileUpload: sidebarInfo.fileUpload || null,
                };
            });
            return { messages: processedMessages, handled: true };
        }
    }
    
    return { handled: true };
};

/**
 * Handle explain_concept tool - display explanation in markdown format
 */
export const handleExplainConceptTraditional = async (response, conversationId) => {
    console.log('🧠 Explain concept tool handler called with response:', response);
    
    // Parse the explanation response data
    let explanationData = null;
    try {
        if (typeof response.response === 'string') {
            explanationData = JSON.parse(response.response);
        } else {
            explanationData = response.response;
        }
        console.log('🧠 Parsed explanation data:', explanationData);
    } catch (error) {
        console.error('Failed to parse explanation response:', error);
        return { handled: false };
    }
    
    if (explanationData && explanationData.explanation) {
        // Strip markdown code block wrapper if present
        let cleanText = explanationData.explanation;
        if (cleanText.startsWith('```markdown\n') && cleanText.endsWith('\n```')) {
            cleanText = cleanText.slice(12, -4); // Remove ```markdown\n and \n```
        } else if (cleanText.startsWith('```markdown\\n') && cleanText.endsWith('\\n```')) {
            cleanText = cleanText.slice(13, -5); // Remove ```markdown\\n and \\n```
        }
        
        // Send the explanation as a message in markdown format
        const aiMessage = {
            sender_id: null,
            sender_username: 'assistant',
            role: 'assistant',
            text: cleanText,
            attachments: [],
            is_markdown: true
        };
        await sendMessageToConversation(conversationId, aiMessage);
        
        // Fetch updated messages from backend
        const convAfterAI = await getConversationById(conversationId);
        if (convAfterAI && Array.isArray(convAfterAI.messages)) {
            const processedMessages = convAfterAI.messages.map(msg => {
                const sidebarInfo = msg.sidebar_info || {};
                return {
                    id: msg.message_id || msg.id || Date.now(),
                    content: msg.text || msg.content,
                    sender: msg.role === 'assistant' ? 'ai' : 'user',
                    timestamp: msg.timestamp || '',
                    conversation_id: msg.conversation_id,
                    fileUpload: sidebarInfo.fileUpload || null,
                };
            });
            return { messages: processedMessages, handled: true };
        }
    }
    
    return { handled: true };
};

/**
 * Handle generate_question_paper tool - display QA pairs in right sidebar
 */
export const handleQuestionPaperTraditional = async (response, conversationId, params) => {
    const { setQaPairs, setCurrentTool, setRightSidebarOpen, settings } = params;
    
    console.log('📝 Question paper tool handler called with response:', response);
    console.log('📝 Settings:', settings);
    console.log('📝 Available params:', Object.keys(params));
    console.log('📝 setQaPairs function:', typeof setQaPairs);
    console.log('📝 setRightSidebarOpen function:', typeof setRightSidebarOpen);
    
    // Parse the question paper response data
    let qaData = null;
    try {
        if (typeof response.response === 'string') {
            qaData = JSON.parse(response.response);
        } else {
            qaData = response.response;
        }
        console.log('📝 Parsed question paper data:', qaData);
    } catch (error) {
        console.error('Failed to parse question paper response:', error);
        return { handled: false };
    }
    
    if (qaData && qaData.qa_pairs) {
        console.log('📝 Found question paper, setting state...');
        console.log('📝 QA pairs count:', qaData.qa_pairs.length);
        
        // Clear other tool data first, then set QA pairs
        clearOtherToolData('qaPairs', params);
        console.log('📝 Setting QA pairs...');
        setQaPairs(qaData);
        
        console.log('📝 Setting current tool to Tools...');
        setCurrentTool('Tools');
        
        console.log('📝 showRightSidebar setting:', settings.showRightSidebar);
        console.log('📝 setRightSidebarOpen function available:', typeof setRightSidebarOpen === 'function');
        
        if (settings.showRightSidebar !== false) {
            console.log('📝 Opening right sidebar...');
            setRightSidebarOpen(true);
            console.log('📝 Right sidebar open command sent');
        } else {
            console.log('📝 Right sidebar disabled in settings');
        }
        
        // Send confirmation message
        const confirmationText = `📝 Generated question paper with ${qaData.qa_pairs.length} questions on ${qaData.content_preview}. Test your knowledge in the sidebar!`;
        const aiMessage = {
            sender_id: null,
            sender_username: 'assistant',
            role: 'assistant',
            text: confirmationText,
            attachments: [],
            sidebar_info: {
                tool_name: 'generate_question_paper',
                qaPairs: qaData,
                sidebar_opened: true,
                sidebar_context: 'question_paper'
            }
        };
        await sendMessageToConversation(conversationId, aiMessage);
        
        // Fetch updated messages from backend
        const convAfterAI = await getConversationById(conversationId);
        if (convAfterAI && Array.isArray(convAfterAI.messages)) {
            const processedMessages = convAfterAI.messages.map(msg => {
                const sidebarInfo = msg.sidebar_info || {};
                return {
                    id: msg.message_id || msg.id || Date.now(),
                    content: msg.text || msg.content,
                    sender: msg.role === 'assistant' ? 'ai' : 'user',
                    timestamp: msg.timestamp || '',
                    conversation_id: msg.conversation_id,
                    flashcards: sidebarInfo.flashcards || null,
                    topicBreakdown: sidebarInfo.topicBreakdown || null,
                    keyConcepts: sidebarInfo.keyConcepts || null,
                    mcqSet: sidebarInfo.mcqSet || null,
                    qaPairs: sidebarInfo.qaPairs || null,
                    fileUpload: sidebarInfo.fileUpload || null,
                };
            });
            return { messages: processedMessages, handled: true };
        }
    }
    
    return { handled: true };
};

/**
 * Handle study_plan tool - display study plan in right sidebar
 */
export const handleStudyPlanTraditional = async (response, conversationId, params) => {
    const { setStudyPlan, setCurrentTool, setRightSidebarOpen, settings } = params;
    
    console.log('📚 Study plan tool handler called with response:', response);
    console.log('📚 Settings:', settings);
    console.log('📚 Available params:', Object.keys(params));
    console.log('📚 setStudyPlan function:', typeof setStudyPlan);
    console.log('📚 setRightSidebarOpen function:', typeof setRightSidebarOpen);
    
    // Parse the study plan response data
    let studyPlanData = null;
    try {
        if (typeof response.response === 'string') {
            studyPlanData = JSON.parse(response.response);
        } else {
            studyPlanData = response.response;
        }
        console.log('📚 Parsed study plan data:', studyPlanData);
    } catch (error) {
        console.error('Failed to parse study plan response:', error);
        return { handled: false };
    }
    
    if (studyPlanData && studyPlanData.study_sessions) {
        console.log('📚 Found study plan, setting state...');
        console.log('📚 Study sessions count:', studyPlanData.study_sessions.length);
        
        // Clear other tool data first, then set study plan
        clearOtherToolData('studyPlan', params);
        console.log('📚 Setting study plan...');
        setStudyPlan(studyPlanData);
        
        console.log('📚 Setting current tool to Tools...');
        setCurrentTool('Tools');
        
        console.log('📚 showRightSidebar setting:', settings.showRightSidebar);
        console.log('📚 setRightSidebarOpen function available:', typeof setRightSidebarOpen === 'function');
        
        if (settings.showRightSidebar !== false) {
            console.log('📚 Opening right sidebar...');
            setRightSidebarOpen(true);
            console.log('📚 Right sidebar open command sent');
        } else {
            console.log('📚 Right sidebar disabled in settings');
        }
        
        // Send confirmation message
        const confirmationText = `📚 Generated ${studyPlanData.total_days}-day study plan for ${studyPlanData.subject_area} (${studyPlanData.total_hours} total hours). Check it out in the sidebar!`;
        const aiMessage = {
            sender_id: null,
            sender_username: 'assistant',
            role: 'assistant',
            text: confirmationText,
            attachments: [],
            sidebar_info: {
                tool_name: 'study_plan',
                studyPlan: studyPlanData,
                sidebar_opened: true,
                sidebar_context: 'study_plan'
            }
        };
        await sendMessageToConversation(conversationId, aiMessage);
        
        // Fetch updated messages from backend
        const convAfterAI = await getConversationById(conversationId);
        if (convAfterAI && Array.isArray(convAfterAI.messages)) {
            const processedMessages = convAfterAI.messages.map(msg => {
                const sidebarInfo = msg.sidebar_info || {};
                return {
                    id: msg.message_id || msg.id || Date.now(),
                    content: msg.text || msg.content,
                    sender: msg.role === 'assistant' ? 'ai' : 'user',
                    timestamp: msg.timestamp || '',
                    conversation_id: msg.conversation_id,
                    flashcards: sidebarInfo.flashcards || null,
                    topicBreakdown: sidebarInfo.topicBreakdown || null,
                    keyConcepts: sidebarInfo.keyConcepts || null,
                    mcqSet: sidebarInfo.mcqSet || null,
                    qaPairs: sidebarInfo.qaPairs || null,
                    studyPlan: sidebarInfo.studyPlan || null,
                    fileUpload: sidebarInfo.fileUpload || null,
                };
            });
            return { messages: processedMessages, handled: true };
        }
    }
    
    return { handled: true };
};

/**
 * Handle build_visual tool - display visual flowcharts in right sidebar
 */
export const handleBuildVisualTraditional = async (response, conversationId, params) => {
    const { setVisualData, setCurrentTool, setRightSidebarOpen, settings } = params;
    
    console.log('📊 Build visual tool handler called with response:', response);
    console.log('📊 Settings:', settings);
    console.log('📊 Available params:', Object.keys(params));
    console.log('📊 setVisualData function:', typeof setVisualData);
    console.log('📊 setRightSidebarOpen function:', typeof setRightSidebarOpen);
    
    // Parse the visual response data
    let visualData = null;
    try {
        if (typeof response.response === 'string') {
            visualData = JSON.parse(response.response);
        } else {
            visualData = response.response;
        }
        console.log('📊 Parsed visual data:', visualData);
    } catch (error) {
        console.error('Failed to parse visual response:', error);
        return { handled: false };
    }
    
    if (visualData && (visualData.elements || visualData.visual_type)) {
        console.log('📊 Found visual data, setting state...');
        console.log('📊 Visual type:', visualData.visual_type);
        console.log('📊 Elements count:', visualData.elements?.length || 0);
        
        // Clear other tool data first, then set visual data
        clearOtherToolData('visualData', params);
        console.log('📊 Setting visual data...');
        setVisualData(visualData);
        
        console.log('📊 Setting current tool to Tools...');
        setCurrentTool('Tools');
        
        console.log('📊 showRightSidebar setting:', settings.showRightSidebar);
        console.log('📊 setRightSidebarOpen function available:', typeof setRightSidebarOpen === 'function');
        
        if (settings.showRightSidebar !== false) {
            console.log('📊 Opening right sidebar...');
            setRightSidebarOpen(true);
            console.log('📊 Right sidebar open command sent');
        } else {
            console.log('📊 Right sidebar disabled in settings');
        }
        
        // Send confirmation message
        const confirmationText = `📊 Generated ${visualData.visual_type || 'visual'}: "${visualData.title || 'Untitled'}". Check it out in the sidebar!`;
        const aiMessage = {
            sender_id: null,
            sender_username: 'assistant',
            role: 'assistant',
            text: confirmationText,
            attachments: [],
            sidebar_info: {
                tool_name: 'build_visual',
                visualData: visualData,
                sidebar_opened: true,
                sidebar_context: 'visual'
            }
        };
        await sendMessageToConversation(conversationId, aiMessage);
        
        // Fetch updated messages from backend
        const convAfterAI = await getConversationById(conversationId);
        if (convAfterAI && Array.isArray(convAfterAI.messages)) {
            const processedMessages = convAfterAI.messages.map(msg => {
                const sidebarInfo = msg.sidebar_info || {};
                return {
                    id: msg.message_id || msg.id || Date.now(),
                    content: msg.text || msg.content,
                    sender: msg.role === 'assistant' ? 'ai' : 'user',
                    timestamp: msg.timestamp || '',
                    conversation_id: msg.conversation_id,
                    flashcards: sidebarInfo.flashcards || null,
                    topicBreakdown: sidebarInfo.topicBreakdown || null,
                    keyConcepts: sidebarInfo.keyConcepts || null,
                    mcqSet: sidebarInfo.mcqSet || null,
                    qaPairs: sidebarInfo.qaPairs || null,
                    studyPlan: sidebarInfo.studyPlan || null,
                    visualData: sidebarInfo.visualData || null,
                    fileUpload: sidebarInfo.fileUpload || null,
                };
            });
            return { messages: processedMessages, handled: true };
        }
    }
    
    return { handled: true };
};

/**
 * Test function to manually trigger visual flowchart (for debugging)
 * Usage: You can call this from browser console to test the visual functionality
 */
export const testBuildVisual = async (params) => {
    console.log('🧪 Testing visual flowchart with params:', params);
    
    const testResponse = {
        tool: "build_visual",
        response: {
            "visual_type": "flowchart",
            "title": "Supervised Learning Overview",
            "description": "A beginner-friendly guide to the key steps in supervised learning.",
            "elements": [
                {
                    "id": "start",
                    "label": "Begin Supervised Learning",
                    "type": "start"
                },
                {
                    "id": "data_collection",
                    "label": "Collect Data",
                    "type": "process",
                    "parent": "start"
                },
                {
                    "id": "data_preprocessing",
                    "label": "Preprocess Data",
                    "type": "process",
                    "parent": "data_collection"
                },
                {
                    "id": "choose_algorithm",
                    "label": "Select Algorithm",
                    "type": "process",
                    "parent": "data_preprocessing"
                },
                {
                    "id": "train_model",
                    "label": "Train Model",
                    "type": "process",
                    "parent": "choose_algorithm"
                },
                {
                    "id": "evaluate_model",
                    "label": "Evaluate Model",
                    "type": "process",
                    "parent": "train_model"
                },
                {
                    "id": "improve_model",
                    "label": "Improve Model?",
                    "type": "decision",
                    "parent": "evaluate_model"
                },
                {
                    "id": "end",
                    "label": "Deploy Model",
                    "type": "end",
                    "parent": "improve_model"
                }
            ]
        }
    };
    
    console.log('🧪 Calling handleBuildVisualTraditional...');
    const result = await handleBuildVisualTraditional(testResponse, params.conversationId, params);
    console.log('🧪 Test result:', result);
    return result;
};

/**
 * Test function to manually trigger study plan (for debugging)
 * Usage: You can call this from browser console to test the study plan functionality
 */
export const testStudyPlan = async (params) => {
    console.log('🧪 Testing study plan with params:', params);
    
    const testResponse = {
        tool: "study_plan",
        response: {
            "study_sessions": [
                {
                    "day": 1,
                    "date": "2025-08-25",
                    "duration_hours": 2.0,
                    "topics": ["Introduction to Supervised Learning", "Types of Supervised Learning"],
                    "activities": ["Read introductory articles", "Watch video lectures"],
                    "resources": ["Online articles", "YouTube lectures"],
                    "priority": "high",
                    "estimated_difficulty": "easy",
                    "learning_objectives": ["Understand the basic concepts of supervised learning", "Differentiate between types of supervised learning"]
                },
                {
                    "day": 2,
                    "date": "2025-08-26",
                    "duration_hours": 2.0,
                    "topics": ["Linear Regression", "Logistic Regression"],
                    "activities": ["Read textbook chapters", "Implement simple models"],
                    "resources": ["Machine Learning textbook", "Python tutorials"],
                    "priority": "medium",
                    "estimated_difficulty": "moderate",
                    "learning_objectives": ["Implement linear regression in Python", "Understand logistic regression applications"]
                }
            ],
            "subject_area": "machine learning",
            "knowledge_level": "intermediate",
            "total_days": 2,
            "total_hours": 4.0,
            "learning_goals": ["Understand the main ideas", "Implement basic algorithms", "Evaluate model performance"],
            "deadline": null
        }
    };
    
    console.log('🧪 Calling handleStudyPlanTraditional...');
    const result = await handleStudyPlanTraditional(testResponse, params.conversationId, params);
    console.log('🧪 Test result:', result);
    return result;
};

/**
 * Test function to manually trigger question paper (for debugging)
 * Usage: You can call this from browser console to test the question paper functionality
 */
export const testQuestionPaper = async (params) => {
    console.log('🧪 Testing question paper with params:', params);
    
    const testResponse = {
        tool: "generate_question_paper",
        response: {
            "document_id": null,
            "content_preview": "supervised learning in machine learning",
            "qa_pairs": [
                {
                    "question": "What is supervised learning in machine learning?",
                    "answer": "Supervised learning is a type of machine learning where a model is trained on labeled data, meaning the input data is paired with the correct output."
                },
                {
                    "question": "What are the two main types of supervised learning tasks?",
                    "answer": "The two main types of supervised learning tasks are classification, where the output is a category, and regression, where the output is a continuous value."
                },
                {
                    "question": "How does a supervised learning algorithm learn from data?",
                    "answer": "A supervised learning algorithm learns by using labeled training data to make predictions and adjusting its parameters to minimize the difference between its predictions and the actual outcomes."
                }
            ]
        }
    };
    
    console.log('🧪 Calling handleQuestionPaperTraditional...');
    const result = await handleQuestionPaperTraditional(testResponse, params.conversationId, params);
    console.log('🧪 Test result:', result);
    return result;
};

/**
 * Test function to manually trigger flashcards (for debugging)
 */
export const testFlashcards = async (params) => {
    const testResponse = {
        tool: "generate_flashcards",
        response: {
            "flashcards": [
                {
                    "question": "What distinguishes supervised learning from unsupervised learning in machine learning?",
                    "answer": "Supervised learning uses labeled data to train models, meaning each input has a corresponding output label, whereas unsupervised learning works with unlabeled data to find hidden patterns or intrinsic structures."
                },
                {
                    "question": "How does a supervised learning algorithm use labeled data to make predictions?",
                    "answer": "A supervised learning algorithm learns a mapping function from the input features to the output labels by minimizing the error between the predicted and actual labels, allowing it to make predictions on new, unseen data."
                }
            ],
            "subject_area": "machine learning",
            "difficulty_level": "intermediate",
            "total_cards": 2
        }
    };
    
    return await handleFlashcardsTraditional(testResponse, params.conversationId, params);
};

/**
 * TRADITIONAL TOOL DISPATCHER
 * Routes traditional tools to their specific handlers
 */
export const handleTraditionalTools = async (response, params) => {
    const {
        conversationId,
    } = params;

    console.log('🔧 Tool dispatcher called with tool:', response.tool);

    switch (response.tool) {
        case 'bramha':
            return await handleBramhaTraditional(response, conversationId);

        case 'generate_flashcards':
            return await handleFlashcardsTraditional(response, conversationId, params);

        case 'topic_breakdown':
            return await handleTopicBreakdownTraditional(response, conversationId, params);

        case 'extract_key_concepts':
            return await handleKeyConceptsTraditional(response, conversationId, params);

        case 'generate_mcq_set':
            return await handleMCQSetTraditional(response, conversationId, params);

        case 'explain_concept':
            return await handleExplainConceptTraditional(response, conversationId, params);

        case 'generate_question_paper':
            return await handleQuestionPaperTraditional(response, conversationId, params);

        case 'study_plan':
            return await handleStudyPlanTraditional(response, conversationId, params);

        case 'build_visual':
            return await handleBuildVisualTraditional(response, conversationId, params);

        // Add more traditional tools here
        // case 'generate_summary':
        //     return await handleSummaryTool(response, conversationId);
        
        // case 'translate_text':
        //     return await handleTranslateTool(response, conversationId);
            
        default:
            console.log('🔧 Tool not handled:', response.tool);
            // Tool not handled by specific handlers
            return { handled: false };
    }
};