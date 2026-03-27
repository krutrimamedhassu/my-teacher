import React, { useState } from 'react';
import { Box, Typography, Paper } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { convertTextToSpeechStreaming, playAudioFromBlob } from '../../services/speech/speechService';

const MessageBubble = ({ message, theme }) => {
  console.log('💬 MessageBubble: Rendering message:', {
    id: message.id,
    sender: message.sender,
    contentLength: message.content?.length || 0,
    timestamp: message.timestamp
  });

  const [copySuccess, setCopySuccess] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  const handleCopy = async () => {
    console.log('📋 MessageBubble: Copy button clicked for message:', message.id);
    try {
      if (navigator && navigator.clipboard) {
        const textToCopy = typeof message.content === 'string' ? message.content : '';
        console.log('📋 MessageBubble: Copying text to clipboard, length:', textToCopy.length);
        await navigator.clipboard.writeText(textToCopy);

        // Haptic feedback
        if (navigator.vibrate) {
          navigator.vibrate(50); // Short vibration
          console.log('📋 MessageBubble: Haptic feedback triggered');
        }

        // Show tick icon
        console.log('📋 MessageBubble: Setting copy success to true');
        setCopySuccess(true);

        // Reset after 2 seconds
        setTimeout(() => {
          console.log('📋 MessageBubble: Resetting copy success to false');
          setCopySuccess(false);
        }, 2000);
      }
    } catch (error) {
      console.error('❌ MessageBubble: Failed to copy:', error);
    }
  };

  const handleSpeaker = async () => {
    console.log('🔊 MessageBubble: Speaker button clicked for message:', message.id);

    if (isPlayingAudio) {
      console.log('🔊 MessageBubble: Audio already playing, ignoring click');
      return;
    }

    try {
      const textToSpeak = typeof message.content === 'string' ? message.content : '';

      if (!textToSpeak || textToSpeak.trim().length === 0) {
        console.warn('⚠️ MessageBubble: No text to speak');
        return;
      }

      console.log('🔊 MessageBubble: Converting text to speech (STREAMING), length:', textToSpeak.length);
      setIsPlayingAudio(true);

      // Use streaming TTS for faster response (3-5s for long text vs 45s for non-streaming)
      const audioBlob = await convertTextToSpeechStreaming(textToSpeak);
      console.log('🔊 MessageBubble: Audio blob received from streaming endpoint, playing...');

      // Haptic feedback
      if (navigator.vibrate) {
        navigator.vibrate(50);
        console.log('🔊 MessageBubble: Haptic feedback triggered');
      }

      // Play audio
      await playAudioFromBlob(audioBlob);
      console.log('✅ MessageBubble: Audio playback completed');
    } catch (error) {
      console.error('❌ MessageBubble: TTS error:', error);
      alert('Failed to play audio. Please try again.');
    } finally {
      setIsPlayingAudio(false);
    }
  };

  return (
    <Box
      sx={{
        maxWidth: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: message.sender === 'user' ? 'flex-end' : 'flex-start',
        mb: 3
      }}
    >
      {message.sender === 'user' ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 1, maxWidth: '100%' }}>
          {/* Show document attachments if any */}
          {message.attachments && message.attachments.length > 0 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, maxWidth: '100%' }}>
              {message.attachments.map((attachment, index) => (
                <Paper
                  key={attachment.name || `attachment-${index}`}
                  elevation={0}
                  sx={{
                    py: 1.5,
                    px: 2,
                    bgcolor: '#f8f9fa',
                    borderRadius: '12px',
                    border: '1px solid #e0e0e0',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.5,
                    minWidth: '280px',
                    maxWidth: '400px'
                  }}
                >
                  <Box sx={{ fontSize: '24px' }}>
                    {attachment.file_type?.includes('pdf') ? '📄' : 
                     attachment.file_type?.includes('doc') ? '📝' : 
                     attachment.file_type?.includes('text') ? '📃' : 
                     attachment.file_type?.includes('html') ? '🌐' : '📄'}
                  </Box>
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        fontWeight: 600,
                        color: theme.palette.text.primary,
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis'
                      }}
                    >
                      {attachment.filename}
                    </Typography>
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        color: theme.palette.text.secondary,
                        display: 'block'
                      }}
                    >
                      {attachment.filesize ? `${Math.round(attachment.filesize / 1024)} KB` : 'Document'}
                    </Typography>
                  </Box>
                </Paper>
              ))}
            </Box>
          )}
          
          {/* Show text message if any */}
          {message.content && (
            <Paper
              elevation={0}
              sx={{
                py: 1,
                px: 2,
                bgcolor: message.isFileUpload ? '#f8f9fa' : '#f5f5f5',
                color: theme.palette.text.primary,
                borderRadius: '20px',
                maxWidth: '100%',
                border: message.isFileUpload ? '1px solid #e0e0e0' : 'none'
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {message.isFileUpload && (
                  <img src="/stacked-books.svg" alt="File" width="16" height="16" />
                )}
                <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                  {message.content}
                </Typography>
              </Box>
            </Paper>
          )}
        </Box>
      ) : (
        <>
          <Typography 
            variant="body1" 
            sx={{ 
              color: theme.palette.text.primary,
              lineHeight: 1.6
            }}
          >
            {message.isRawHTML ? (
              // Render JSX content directly for special messages like limit errors
              message.content
            ) : (
              // Render markdown content normally
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkBreaks, remarkMath]}
                rehypePlugins={[rehypeKatex]}
                components={{
                  p: ({ children }) => (
                    <Typography variant="body1" sx={{ mb: 1 }}>
                      {children}
                    </Typography>
                  ),
                  code: ({ node, inline, className, children, ...props }) => {
                    return !inline ? (
                      <Box className="code-block">
                        <pre>
                          <code {...props}>
                            {children}
                          </code>
                        </pre>
                      </Box>
                    ) : (
                      <code className="inline-code" {...props}>
                        {children}
                      </code>
                    );
                  },
                  a: ({ children, href }) => (
                    <a href={href} className="message-link" target="_blank" rel="noopener noreferrer">
                      {children}
                    </a>
                  ),
                  ul: ({ children }) => (
                    <ul className="message-list">
                      {children}
                    </ul>
                  ),
                  li: ({ children }) => (
                    <li className="message-list-item">
                      {children}
                    </li>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="message-blockquote">
                      {children}
                    </blockquote>
                  ),
                  table: ({ children }) => (
                    <table className="message-table">
                      {children}
                    </table>
                  )
                }}
              >
                {message.content}
              </ReactMarkdown>
            )}
          </Typography>
          {/* Hide action buttons for limit error messages */}
          {!message.isLimitError && (
            <Box className="message-actions-row">
              <Box
                component="span"
                sx={{
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'flex-start',
                  '&:hover': { opacity: 0.7 },
                  transition: 'all 0.2s ease-in-out'
                }}
                aria-label={copySuccess ? "Copied!" : "Copy message"}
                onClick={handleCopy}
              >
                {copySuccess ? (
                  <Box
                    sx={{
                      width: 20,
                      height: 20,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#666666',
                      fontSize: '16px',
                      fontWeight: 'bold'
                    }}
                  >
                    ✓
                  </Box>
                ) : (
                  <img
                    src="/copy-icon.svg"
                    alt="Copy"
                    height={20}
                    style={{ verticalAlign: 'top', display: 'inline-block' }}
                  />
                )}
              </Box>
              <Box
                component="span"
                sx={{
                  cursor: isPlayingAudio ? 'not-allowed' : 'pointer',
                  display: 'inline-flex',
                  alignItems: 'flex-start',
                  '&:hover': { opacity: isPlayingAudio ? 1 : 0.7 },
                  transition: 'all 0.2s ease-in-out',
                  opacity: isPlayingAudio ? 0.5 : 1,
                  marginLeft: '1.5px'
                }}
                aria-label={isPlayingAudio ? "Playing..." : "Read aloud"}
                onClick={handleSpeaker}
              >
                <img
                  src="/speaker-icon.svg"
                  alt={isPlayingAudio ? "Playing" : "Read aloud"}
                  height={20}
                  style={{
                    verticalAlign: 'top',
                    display: 'inline-block',
                    animation: isPlayingAudio ? 'pulse-speaker 1s ease-in-out infinite' : 'none'
                  }}
                />
              </Box>
              <img src="/thumbs-up.svg" alt="Thumbs up" height={20} style={{ cursor: 'pointer', verticalAlign: 'top', display: 'inline-block', marginTop: '-2px' }} />
              <img src="/thumbs-down.svg" alt="Thumbs down" height={20} style={{ cursor: 'pointer', verticalAlign: 'top', display: 'inline-block', marginLeft: '1.5px' }} />
            </Box>
          )}
        </>
      )}
    </Box>
  );
};

export default React.memo(MessageBubble); 