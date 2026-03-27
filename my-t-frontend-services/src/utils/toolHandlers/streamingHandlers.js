/**
 * STREAMING MODE TOOL HANDLERS
 * Handles tools with special streaming effects (word-by-word, real-time, etc.)
 */

import { sendMessageToConversation, getConversationById } from '../../services';

/**
 * Handle bramha tool with streaming effect (word-by-word)
 */
export const handleBramhaStreaming = async (response, setStreamingContent, conversationId) => {
    const finalText = typeof response.response === 'string' ? response.response : JSON.stringify(response.response);
    const words = finalText.split(/\s+/);
    let assembled = '';
    
    // Show words progressively with typing effect
    for (let i = 0; i < words.length; i++) {
        assembled += (i === 0 ? '' : ' ') + words[i];
        setStreamingContent(assembled);
        // eslint-disable-next-line no-await-in-loop
        await new Promise(r => setTimeout(r, Math.min(60, Math.max(20, Math.floor(finalText.length / 120)))));
    }
    
    // Persist the streamed AI message after completion
    const aiMessage = {
        sender_id: null,
        sender_username: 'assistant',
        role: 'assistant',
        text: finalText,
        attachments: []
    };
    await sendMessageToConversation(conversationId, aiMessage);
    
    // Fetch updated messages from backend
    const convAfterAIStream = await getConversationById(conversationId);
    if (convAfterAIStream && Array.isArray(convAfterAIStream.messages)) {
        const processedMessages = convAfterAIStream.messages.map(msg => {
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
        setStreamingContent('');
        return { messages: processedMessages, handled: true };
    }
    setStreamingContent('');
    return { handled: true };
};

/**
 * Handle live coding tool with streaming effect (future tool example)
 */
export const handleLiveCodingStreaming = async (response, setStreamingContent, conversationId) => {
    // Example for future streaming tool
    const code = response.response;
    const lines = code.split('\n');
    let assembled = '';
    
    // Show code line by line
    for (let i = 0; i < lines.length; i++) {
        assembled += (i === 0 ? '' : '\n') + lines[i];
        setStreamingContent(assembled);
        // eslint-disable-next-line no-await-in-loop
        await new Promise(r => setTimeout(r, 150)); // Slower for code readability
    }
    
    const aiMessage = {
        sender_id: null,
        sender_username: 'assistant',
        role: 'assistant',
        text: code,
        attachments: []
    };
    await sendMessageToConversation(conversationId, aiMessage);
    setStreamingContent('');
    return { handled: true };
};

/**
 * Handle explain_concept tool with streaming effect (word-by-word)
 */
export const handleExplainConceptStreaming = async (response, setStreamingContent, conversationId) => {
    // Parse the explanation response data
    let explanationData = null;
    try {
        if (typeof response.response === 'string') {
            explanationData = JSON.parse(response.response);
        } else {
            explanationData = response.response;
        }
    } catch (error) {
        console.error('Failed to parse explanation response:', error);
        return { handled: false };
    }
    
    if (explanationData && explanationData.explanation) {
        // Strip markdown code block wrapper if present
        let finalText = explanationData.explanation;
        if (finalText.startsWith('```markdown\n') && finalText.endsWith('\n```')) {
            finalText = finalText.slice(12, -4); // Remove ```markdown\n and \n```
        } else if (finalText.startsWith('```markdown\\n') && finalText.endsWith('\\n```')) {
            finalText = finalText.slice(13, -5); // Remove ```markdown\\n and \\n```
        }
        
        const words = finalText.split(/\s+/);
        let assembled = '';
        
        // Show words progressively with typing effect
        for (let i = 0; i < words.length; i++) {
            assembled += (i === 0 ? '' : ' ') + words[i];
            setStreamingContent(assembled);
            // eslint-disable-next-line no-await-in-loop
            await new Promise(r => setTimeout(r, Math.min(60, Math.max(20, Math.floor(finalText.length / 120)))));
        }
        
        // Persist the streamed AI message after completion in markdown format
        const aiMessage = {
            sender_id: null,
            sender_username: 'assistant',
            role: 'assistant',
            text: finalText,
            attachments: [],
            is_markdown: true
        };
        await sendMessageToConversation(conversationId, aiMessage);
        
        // Fetch updated messages from backend
        const convAfterAIStream = await getConversationById(conversationId);
        if (convAfterAIStream && Array.isArray(convAfterAIStream.messages)) {
            const processedMessages = convAfterAIStream.messages.map(msg => {
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
            setStreamingContent('');
            return { messages: processedMessages, handled: true };
        }
        setStreamingContent('');
        return { handled: true };
    }
    
    return { handled: false };
};

/**
 * STREAMING TOOL DISPATCHER
 * Routes streaming tools to their specific handlers
 */
export const handleStreamingTools = async (response, params) => {
    const { conversationId, setStreamingContent } = params;

    switch (response.tool) {
        case 'bramha':
            return await handleBramhaStreaming(response, setStreamingContent, conversationId);
            
        case 'explain_concept':
            return await handleExplainConceptStreaming(response, setStreamingContent, conversationId);
            
        // Add more streaming-specific tools here
        // case 'real_time_analysis':
        //     return await handleRealTimeAnalysisStreaming(response, setStreamingContent, conversationId);
        
        // case 'progressive_chart':
        //     return await handleProgressiveChartStreaming(response, setStreamingContent, conversationId);
            
        default:
            // Tool doesn't have streaming behavior
            return { handled: false };
    }
};