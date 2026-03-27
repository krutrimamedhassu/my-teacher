/**
 * MAIN TOOL HANDLER DISPATCHER
 * Routes tools to streaming vs traditional handlers based on user settings
 */

import { handleStreamingTools } from './streamingHandlers';
import { handleTraditionalTools } from './traditionalHandlers';

/**
 * Main tool handler that routes to streaming vs traditional handlers
 * Add new tools by updating the appropriate handler file in this directory
 */
export const handleToolResponse = async (response, params) => {
    const { settings } = params;

    // Route to streaming or traditional handler based on settings
    if (settings.streamingMode === 'streaming') {
        const streamingResult = await handleStreamingTools(response, params);
        if (streamingResult.handled) {
            return streamingResult;
        }
        // If tool doesn't have streaming behavior, fall back to traditional
        return await handleTraditionalTools(response, params);
    } else {
        // Traditional mode
        return await handleTraditionalTools(response, params);
    }
};