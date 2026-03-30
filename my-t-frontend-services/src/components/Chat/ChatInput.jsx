import React, { useRef, useState, useEffect } from 'react';
import { Box, TextField, IconButton, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { startRecording, stopStream, sendAudioForTranscription } from '../../services/speech/speechService';

const ChatInput = ({ inputValue, setInputValue, handleSendMessage, handleKeyPress, isTyping, inputRef, theme, isMobile, onFileUpload, hasMessages = false, onFilesAttachedChange, isReadOnly = false }) => {
    console.log('💬 ChatInput: Component rendered with props:', {
        inputValue: inputValue?.substring(0, 50) + (inputValue?.length > 50 ? '...' : ''),
        isTyping,
        isMobile
    });

    const fileInputRef = useRef(null);
    const [selectedFiles, setSelectedFiles] = useState([]);

    // Audio recording state
    const [isRecording, setIsRecording] = useState(false);
    const [isTranscribing, setIsTranscribing] = useState(false);
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const streamRef = useRef(null);

    // Load persisted file data on component mount
    useEffect(() => {
        try {
            const persistedData = localStorage.getItem('chatInput_selectedFiles');
            if (persistedData) {
                const parsedData = JSON.parse(persistedData);
                console.log('🔄 ChatInput: Restoring persisted file data:', parsedData);
                
                // Create placeholder file items for display (without actual File objects)
                const restoredItems = parsedData.map(item => ({
                    ...item,
                    file: null, // File object can't be restored, will need re-selection for upload
                    isPersisted: true // Flag to identify restored files
                }));
                setSelectedFiles(restoredItems);
            }
        } catch (error) {
            console.error('❌ ChatInput: Error loading persisted files:', error);
            localStorage.removeItem('chatInput_selectedFiles'); // Clear corrupted data
        }
    }, []);

    // Persist file data whenever selectedFiles changes
    useEffect(() => {
        if (selectedFiles.length > 0) {
            const dataToSave = selectedFiles.map(fileItem => ({
                id: fileItem.id,
                displayName: fileItem.displayName,
                extension: fileItem.extension,
                timestamp: new Date().toISOString(),
                // Note: File object is not saved, only metadata
            }));
            
            console.log('💾 ChatInput: Persisting file data to localStorage:', dataToSave);
            localStorage.setItem('chatInput_selectedFiles', JSON.stringify(dataToSave));
        } else {
            // Clear localStorage when no files are selected
            console.log('🗑️ ChatInput: Clearing persisted file data');
            localStorage.removeItem('chatInput_selectedFiles');
        }
    }, [selectedFiles]);

    // Enhanced debugging for selectedFiles state changes
    useEffect(() => {
        console.log('📁 ChatInput: selectedFiles state changed:', {
            count: selectedFiles.length,
            files: selectedFiles.map(f => ({ 
                name: f.displayName, 
                ext: f.extension, 
                id: f.id,
                hasFile: !!f.file,
                isPersisted: f.isPersisted || false
            })),
            timestamp: new Date().toISOString()
        });
    }, [selectedFiles]);

    // Notify parent when files are attached/cleared
    useEffect(() => {
        if (typeof onFilesAttachedChange === 'function') {
            onFilesAttachedChange(selectedFiles.length > 0);
        }
    }, [selectedFiles, onFilesAttachedChange]);

    const handleFileSelect = (event) => {
        console.log('📁 ChatInput: handleFileSelect called');
        const files = Array.from(event.target.files);
        console.log('📁 ChatInput: Selected files count:', files.length);
        console.log('📁 ChatInput: Current selectedFiles.length before adding:', selectedFiles.length);
        
        if (files.length === 0) {
            console.log('❌ ChatInput: No files selected');
            return;
        }
        
        const acceptedTypes = ['pdf', 'docx', 'doc', 'txt', 'html', 'htm'];
        const newFileItems = [];
        let rejected = 0;
        let limitReached = false;
        
        for (const file of files) {
            // Check if we've reached the limit
            if (selectedFiles.length + newFileItems.length >= 8) {
                console.log('❌ ChatInput: File limit reached (8), stopping file processing');
                limitReached = true;
                break;
            }
            
            const fileExtension = file.name.split('.').pop().toLowerCase();
            
            if (!acceptedTypes.includes(fileExtension)) {
                console.log('❌ ChatInput: File type not accepted:', fileExtension, 'for file:', file.name);
                rejected++;
                continue;
            }
            
            const fileName = file.name.replace(/\.[^/.]+$/, ""); // Remove extension from display name
            const newFileItem = {
                file,
                id: Date.now() + Math.random(), // Unique ID for concurrent uploads
                displayName: fileName,
                extension: fileExtension
            };
            
            newFileItems.push(newFileItem);
            console.log('✅ ChatInput: Prepared file for upload:', newFileItem.displayName);
        }
        
        // Add all valid files at once
        if (newFileItems.length > 0) {
            console.log(`📁 ChatInput: Adding ${newFileItems.length} files to selectedFiles`);
            setSelectedFiles(prev => {
                const newArray = [...prev, ...newFileItems];
                console.log('📁 ChatInput: selectedFiles will be updated to length:', newArray.length);
                return newArray;
            });
        }
        
        // Log summary
        console.log(`📊 ChatInput: File selection summary - Added: ${newFileItems.length}, Rejected: ${rejected}, Limit reached: ${limitReached}`);
        
        // Reset the input value so the same files can be selected again
        event.target.value = '';
        console.log('📁 ChatInput: Reset file input value');
    };

    const handleSendMessageWithFile = () => {
        console.log('💬 ChatInput: handleSendMessageWithFile called');
        console.log('💬 ChatInput: selectedFiles.length:', selectedFiles.length);
        console.log('💬 ChatInput: onFileUpload available:', !!onFileUpload);
        
        // Check if we have actual files to upload (not just persisted metadata)
        const filesWithActualData = selectedFiles.filter(f => f.file && !f.isPersisted);
        const persistedFilesCount = selectedFiles.filter(f => f.isPersisted && !f.file).length;
        
        console.log('📁 ChatInput: Files with data:', filesWithActualData.length);
        console.log('📁 ChatInput: Persisted files needing re-selection:', persistedFilesCount);
        
        if (filesWithActualData.length > 0 && onFileUpload) {
            console.log('📁 ChatInput: Calling onFileUpload with multiple files and message');
            console.log('📁 ChatInput: Files being uploaded:', filesWithActualData.map(f => f.displayName));
            
            // Prepare visual display data for consistent rendering
            const visualDisplayData = filesWithActualData.map(fileItem => ({
                id: fileItem.id,
                displayName: fileItem.displayName,
                extension: fileItem.extension,
                fileType: getFileTypeDisplay(fileItem.extension),
                fileIcon: getFileIcon(fileItem.extension),
                timestamp: new Date().toISOString(),
                originalFileName: fileItem.file.name,
                fileSize: fileItem.file.size
            }));
            
            console.log('📊 ChatInput: Visual display data:', visualDisplayData);
            
            // Send files with visual metadata - you'll need to update onFileUpload to accept the third parameter
            onFileUpload(filesWithActualData.map(f => f.file), '', visualDisplayData);
            console.log('🚮 ChatInput: Clearing selectedFiles after upload');
            setSelectedFiles([]);
            setInputValue('');
        } else if (persistedFilesCount > 0) {
            console.log('⚠️ ChatInput: Cannot upload - some files need re-selection');
            alert(`Please re-select ${persistedFilesCount} file(s) that were restored from previous session before uploading.`);
        } else {
            console.log('💬 ChatInput: No files to upload, sending regular message');
            handleSendMessage();
        }
    };

    const handleRemoveFile = (fileId) => {
        console.log('📁 ChatInput: Remove file', fileId);
        setSelectedFiles(prev => prev.filter(f => f.id !== fileId));
    };

    const getFileIcon = (extension) => {
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

    const getFileTypeDisplay = (extension) => {
        switch (extension) {
            case 'pdf': return 'PDF';
            case 'docx':
            case 'doc': return 'Document';
            case 'txt': return 'Text';
            case 'html':
            case 'htm': return 'HTML';
            default: return extension.toUpperCase();
        }
    };

    const handleAddButtonClick = () => {
        console.log('➕ ChatInput: Add button clicked');
        fileInputRef.current?.click();
    };

    // Handle clicking on persisted files to re-select them
    const handlePersistedFileClick = (fileItem) => {
        if (fileItem.isPersisted && !fileItem.file) {
            console.log('🔄 ChatInput: Clicking persisted file to re-select:', fileItem.displayName);
            // Remove the persisted item and trigger file selection
            setSelectedFiles(prev => prev.filter(f => f.id !== fileItem.id));
            setTimeout(() => {
                fileInputRef.current?.click();
            }, 100);
        }
    };

    // Handle microphone button click
    const handleMicrophoneClick = async () => {
        console.log('🎤 ChatInput: Microphone button clicked, isRecording:', isRecording);

        if (isRecording) {
            // Stop recording
            console.log('🎤 ChatInput: Stopping recording');
            stopRecording();
        } else {
            // Start recording
            try {
                console.log('🎤 ChatInput: Starting recording');
                const { mediaRecorder, stream } = await startRecording();

                // Store refs
                mediaRecorderRef.current = mediaRecorder;
                streamRef.current = stream;
                audioChunksRef.current = [];

                // Set up event handlers
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        audioChunksRef.current.push(event.data);
                        console.log('🎤 ChatInput: Audio chunk received, size:', event.data.size);
                    }
                };

                mediaRecorder.onstop = async () => {
                    console.log('🎤 ChatInput: MediaRecorder stopped, processing audio');
                    await processRecording();
                };

                // Start recording
                mediaRecorder.start();
                setIsRecording(true);
                console.log('🎤 ChatInput: Recording started');
            } catch (error) {
                console.error('❌ ChatInput: Failed to start recording:', error);
                alert(error.message || 'Failed to access microphone. Please check permissions.');
            }
        }
    };

    // Stop recording
    const stopRecording = () => {
        console.log('🎤 ChatInput: stopRecording called');

        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
            console.log('🎤 ChatInput: MediaRecorder stop triggered');
        }

        // Stop stream
        if (streamRef.current) {
            stopStream(streamRef.current);
            streamRef.current = null;
        }

        setIsRecording(false);
    };

    // Process recorded audio
    const processRecording = async () => {
        console.log('🎤 ChatInput: Processing recording, chunks:', audioChunksRef.current.length);

        if (audioChunksRef.current.length === 0) {
            console.warn('⚠️ ChatInput: No audio chunks recorded');
            return;
        }

        try {
            // Create blob from chunks
            const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
            console.log('🎤 ChatInput: Audio blob created, size:', audioBlob.size);

            // Clear chunks
            audioChunksRef.current = [];

            // Send to backend for transcription
            setIsTranscribing(true);
            console.log('🎤 ChatInput: Sending audio for transcription');

            const response = await sendAudioForTranscription(audioBlob);
            console.log('🎤 ChatInput: Transcription received:', response);

            // Set transcribed text to input
            if (response && response.text) {
                setInputValue(response.text);
                console.log('✅ ChatInput: Transcribed text set to input:', response.text);
            } else {
                throw new Error('No text in transcription response');
            }
        } catch (error) {
            console.error('❌ ChatInput: Transcription error:', error);
            alert('Failed to transcribe audio. Please try again.');
        } finally {
            setIsTranscribing(false);
        }
    };

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (isRecording) {
                stopRecording();
            }
        };
    }, [isRecording]);

    return (
        <Box
            className="chat-input"
            data-has-messages={hasMessages}
            sx={{
                position: 'absolute',
                ...(hasMessages ? {
                    // When messages exist, position at bottom
                    bottom: 15,
                    top: 'auto'
                } : {
                    // When no messages, position 20px above center
                    top: 'calc(50% - 20px)',
                    bottom: 'auto'
                }),
                left: '50%',
                transform: hasMessages ? 'translateX(-50%)' : 'translate(-50%, -50%)',
                width: 'calc(100% - 32px)',
                maxWidth: 'min(778px, calc(100% - 32px))',
                zIndex: 1100,
                transition: 'all 0.3s ease-in-out',
                borderRadius: 3,
                bgcolor: 'white',
                boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
                border: `1px solid ${theme.palette.grey[300]}`,
                overflow: 'hidden',
                '&:focus': {
                    outline: 'none',
                    boxShadow: 'none'
                },
                '&:focus-within': {
                    outline: 'none',
                    boxShadow: 'none'
                }
            }}
        >
            {/* Hidden file input */}
            <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.doc,.txt,.html,.htm"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
                multiple
            />

            {/* Read-only banner for example conversations */}
            {isReadOnly && (
                <Box sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 0.5,
                    py: 0.75,
                    px: 2,
                    bgcolor: theme.palette.grey[50],
                    borderBottom: `1px solid ${theme.palette.grey[200]}`
                }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '13px' }}>
                        This is a read-only example.{' '}
                        <RouterLink
                            to="/register"
                            style={{ color: theme.palette.text.primary, fontWeight: 600, textDecoration: 'underline' }}
                        >
                            Sign up free
                        </RouterLink>
                        {' '}to start your own conversation.
                    </Typography>
                </Box>
            )}

            {/* DEBUG: Visual indicator for selectedFiles state */}
            <Box sx={{ 
                position: 'absolute', 
                top: -25, 
                right: 10, 
                bgcolor: 'red', 
                color: 'white', 
                px: 1, 
                py: 0.5, 
                borderRadius: 1, 
                fontSize: '10px',
                zIndex: 9999,
                display: 'block'
            }}>
                Files: {selectedFiles.length}
            </Box>

            {/* File attachments - shows when files are selected */}
            {selectedFiles.length > 0 && (
                <Box
                    sx={{
                        display: 'flex',
                        overflowX: 'auto',
                        gap: 1,
                        px: 1,
                        py: 1,
                        pt: 1.5,
                        '&::-webkit-scrollbar': {
                            display: 'none'
                        },
                        msOverflowStyle: 'none',
                        scrollbarWidth: 'none'
                    }}
                >
                    {selectedFiles.map((fileItem) => (
                        <Box
                            key={fileItem.id}
                            onClick={() => handlePersistedFileClick(fileItem)}
                            sx={{
                                width: '322px',
                                height: '56px',
                                minWidth: '322px',
                                backgroundColor: fileItem.isPersisted && !fileItem.file 
                                    ? theme.palette.warning.light + '20' 
                                    : theme.palette.grey[50],
                                border: `1px solid ${
                                    fileItem.isPersisted && !fileItem.file 
                                        ? theme.palette.warning.main 
                                        : theme.palette.grey[300]
                                }`,
                                borderRadius: 2,
                                display: 'flex',
                                alignItems: 'center',
                                px: 3,
                                position: 'relative',
                                cursor: fileItem.isPersisted && !fileItem.file ? 'pointer' : 'default',
                                '&:hover .remove-btn': {
                                    opacity: 1
                                },
                                '&:hover': fileItem.isPersisted && !fileItem.file ? {
                                    backgroundColor: theme.palette.warning.light + '40',
                                    borderColor: theme.palette.warning.dark
                                } : {}
                            }}
                        >
                            {/* File icon */}
                            <Box sx={{
                                fontSize: '36px',
                                mr: 3,
                                display: 'flex',
                                alignItems: 'center',
                                position: 'relative'
                            }}>
                                {getFileIcon(fileItem.extension)}
                                {/* Show indicator for persisted files without File object */}
                                {fileItem.isPersisted && !fileItem.file && (
                                    <Box sx={{
                                        position: 'absolute',
                                        top: -4,
                                        right: -4,
                                        width: 12,
                                        height: 12,
                                        bgcolor: 'orange',
                                        borderRadius: '50%',
                                        border: '1px solid white',
                                        fontSize: '8px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        color: 'white'
                                    }}>
                                        !
                                    </Box>
                                )}
                            </Box>

                            {/* File info - two lines */}
                            <Box sx={{ flex: 1, minWidth: 0 }}>
                                <Box sx={{
                                    fontSize: '16px',
                                    fontWeight: 600,
                                    color: theme.palette.text.primary,
                                    whiteSpace: 'nowrap',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    lineHeight: '20px'
                                }}>
                                    {fileItem.displayName.length > 25 ? fileItem.displayName.substring(0, 25) + '...' : fileItem.displayName}
                                </Box>
                                <Box sx={{
                                    fontSize: '14px',
                                    color: fileItem.isPersisted && !fileItem.file 
                                        ? theme.palette.warning.main 
                                        : theme.palette.text.secondary,
                                    lineHeight: '18px',
                                    textTransform: 'uppercase',
                                    fontWeight: 500
                                }}>
                                    {fileItem.isPersisted && !fileItem.file 
                                        ? `${getFileTypeDisplay(fileItem.extension)} - NEEDS RE-SELECT`
                                        : getFileTypeDisplay(fileItem.extension)
                                    }
                                </Box>
                            </Box>

                            {/* Remove button */}
                            <IconButton
                                className="remove-btn"
                                size="small"
                                onClick={() => handleRemoveFile(fileItem.id)}
                                sx={{
                                    position: 'absolute',
                                    top: -6,
                                    right: -6,
                                    width: 24,
                                    height: 24,
                                    minWidth: 24,
                                    backgroundColor: theme.palette.grey[600],
                                    color: 'white',
                                    opacity: 0,
                                    transition: 'opacity 0.2s',
                                    fontSize: '14px',
                                    '&:hover': {
                                        backgroundColor: theme.palette.grey[800]
                                    }
                                }}
                            >
                                ×
                            </IconButton>
                        </Box>
                    ))}
                </Box>
            )}

            {/* Top section with text input - hidden when files are attached */}
            {selectedFiles.length === 0 && (
                <Box sx={{ p: 0, pb: 0, pl: 1, pr: 1 }}>
                    <TextField
                        ref={inputRef}
                        multiline
                        maxRows={3}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSendMessageWithFile();
                            } else {
                                handleKeyPress(e);
                            }
                        }}
                        placeholder={isReadOnly ? "Sign up to start chatting..." : "Ask me anything..."}
                        variant="outlined"
                        fullWidth
                        disabled={isTyping || isReadOnly}
                        sx={{
                            '& .MuiOutlinedInput-root': {
                                borderRadius: 2,
                                bgcolor: 'transparent',
                                '& fieldset': {
                                    border: 'none'
                                },
                                '&:hover fieldset': {
                                    border: 'none'
                                },
                                '&.Mui-focused fieldset': {
                                    border: 'none'
                                },
                                '&.Mui-focused': {
                                    outline: 'none',
                                    boxShadow: 'none'
                                },
                                '&:focus': {
                                    outline: 'none',
                                    boxShadow: 'none'
                                },
                                '&:focus-visible': {
                                    outline: 'none',
                                    boxShadow: 'none'
                                }
                            },
                            '& .MuiInputBase-input': {
                                fontSize: '16px',
                                paddingBottom: '8px',
                                '&:focus': {
                                    outline: 'none',
                                    boxShadow: 'none'
                                },
                                '&:focus-visible': {
                                    outline: 'none',
                                    boxShadow: 'none'
                                }
                            },
                            '& .MuiInputBase-root': {
                                '&.Mui-focused': {
                                    outline: 'none',
                                    boxShadow: 'none'
                                },
                                '&:focus': {
                                    outline: 'none',
                                    boxShadow: 'none'
                                },
                                '&:focus-visible': {
                                    outline: 'none',
                                    boxShadow: 'none'
                                }
                            },
                            '&:focus': {
                                outline: 'none',
                                boxShadow: 'none'
                            },
                            '&:focus-visible': {
                                outline: 'none',
                                boxShadow: 'none'
                            }
                        }}
                    />
                </Box>
            )}

            {/* Bottom section with buttons */}
            <Box
                sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 0.5,
                    p: 0.5,
                    pt: 0,
                    pl: 1,
                    pr: 1,
                    pb: 0.5
                }}
            >
                {/* Add button */}
                <IconButton
                    onClick={handleAddButtonClick}
                    disabled={isTyping || isReadOnly}
                    sx={{
                        width: 40,
                        height: 40,
                        color: theme.palette.text.secondary,
                        '&:hover': {
                            bgcolor: theme.palette.action.hover
                        },
                        '&.Mui-disabled': {
                            color: theme.palette.grey[400]
                        },
                        '&.Mui-focusVisible': {
                            outline: 'none',
                            boxShadow: 'none',
                        }
                    }}
                >
                    <img src="/add-icon.svg" alt="Add" width="24" height="24" />
                </IconButton>

                {/* Spacer to push other buttons to the right */}
                <Box sx={{ flex: 1 }} />

                {/* Voice button */}
                <IconButton
                    onClick={handleMicrophoneClick}
                    disabled={isTyping || isTranscribing || isReadOnly}
                    sx={{
                        width: 40,
                        height: 40,
                        color: isRecording ? '#ef4444' : theme.palette.text.secondary,
                        bgcolor: isRecording ? 'rgba(239, 68, 68, 0.1)' : 'transparent',
                        animation: isRecording ? 'pulse 1.5s ease-in-out infinite' : 'none',
                        '&:hover': {
                            bgcolor: isRecording ? 'rgba(239, 68, 68, 0.2)' : theme.palette.action.hover
                        },
                        '&.Mui-disabled': {
                            color: theme.palette.grey[400]
                        },
                        '&.Mui-focusVisible': {
                            outline: 'none',
                            boxShadow: 'none',
                        },
                        '@keyframes pulse': {
                            '0%, 100%': {
                                opacity: 1,
                            },
                            '50%': {
                                opacity: 0.5,
                            }
                        }
                    }}
                >
                    <img
                        src="/mic-icon.svg"
                        alt={isRecording ? "Stop recording" : isTranscribing ? "Transcribing..." : "Start recording"}
                        width="24"
                        height="24"
                        style={{
                            filter: isRecording ? 'brightness(0) saturate(100%) invert(38%) sepia(85%) saturate(2832%) hue-rotate(343deg) brightness(98%) contrast(88%)' : 'none'
                        }}
                    />
                </IconButton>

                {/* Send button */}
                <IconButton
                    onClick={() => {
                        console.log('💬 ChatInput: Send button clicked');
                        handleSendMessageWithFile();
                    }}
                    disabled={(!inputValue.trim() && selectedFiles.filter(f => f.file && !f.isPersisted).length === 0) || isTyping || isReadOnly}
                    sx={{
                        width: 36,
                        height: 36,
                        bgcolor: 'black',
                        color: 'white',
                        marginTop: '-3px',
                        '&:hover': {
                            bgcolor: '#333',
                            transform: 'scale(1.05)'
                        },
                        '&.Mui-disabled': {
                            bgcolor: theme.palette.grey[300],
                            color: theme.palette.grey[500]
                        },
                        transition: 'all 0.2s ease-in-out',
                        '&.Mui-focusVisible': {
                            outline: 'none',
                            boxShadow: 'none',
                        }
                    }}
                >
                    <img src="/send-icon.svg" alt="Send" width="24" height="24" />
                </IconButton>
            </Box>
        </Box>
    );
};

export default ChatInput; 