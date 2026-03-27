import React from 'react';
import { Box, Typography, CircularProgress } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

const TypingIndicator = ({ theme, streamingContent, isStreaming }) => {
  console.log('⌨️ TypingIndicator: Component rendered');
  console.log('⌨️ TypingIndicator: streamingContent =', streamingContent);
  console.log('⌨️ TypingIndicator: isStreaming =', isStreaming);
  
  // Check if this is a tool call (contains loading message)
  const isToolCall = streamingContent && (streamingContent.includes('🔄') || streamingContent.includes('✅'));
  
  if (isStreaming && streamingContent) {
    return (
      <Box
        sx={{
          maxWidth: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-start',
          mb: 3
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CircularProgress size={16} sx={{ color: theme.palette.primary.main }} />
          <Typography 
            variant="body1" 
            sx={{ 
              color: theme.palette.text.primary,
              lineHeight: 1.6,
              fontStyle: isToolCall ? 'italic' : 'normal',
              fontWeight: isToolCall ? 500 : 400,
              opacity: isToolCall ? 0.8 : 1
            }}
          >
            {isToolCall ? (
              streamingContent
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkBreaks, remarkMath]}
                rehypePlugins={[rehypeKatex]}
                components={{
                  p: ({ children }) => <>{children}</>,
                  code: ({ node, inline, className, children, ...props }) => {
                    return !inline ? (
                      <Box component="pre" sx={{ display: 'inline' }}>
                        <code {...props}>{children}</code>
                      </Box>
                    ) : (
                      <code {...props}>{children}</code>
                    );
                  }
                }}
              >
                {streamingContent}
              </ReactMarkdown>
            )}
          </Typography>
        </Box>
      </Box>
    );
  }
  
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'flex-start',
        mb: 2,
        px: 0,
        pl: 0
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 0.5,
          pl: 0
        }}
      >
        <span className="typing-jump-dot">.</span>
        <span className="typing-jump-dot">.</span>
        <span className="typing-jump-dot">.</span>
      </Box>
    </Box>
  );
};

export default TypingIndicator; 