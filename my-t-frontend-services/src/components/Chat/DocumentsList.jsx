import React from 'react';
import { Box, Typography, List, ListItem, ListItemText, IconButton, Chip } from '@mui/material';
import { Delete as DeleteIcon } from '@mui/icons-material';

const DocumentsList = ({ documents, onDeleteDocument, theme }) => {
  console.log('📄 DocumentsList: Component rendered with', documents?.length || 0, 'documents');
  
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <Box sx={{ 
        height: '100%', 
        overflow: 'auto',
        py: 2,
        '&::-webkit-scrollbar': {
          display: 'none'
        },
        '-ms-overflow-style': 'none',
        'scrollbar-width': 'none'
      }}>
      
      {documents.length === 0 ? (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mt: 4 }}>
          No documents uploaded yet.
          <br />
          Use the + button to upload a file.
        </Typography>
      ) : (
        <List sx={{ p: 0 }}>
          {documents.map((doc) => (
            <ListItem
              key={doc.id}
              sx={{
                border: `1px solid ${theme.palette.divider}`,
                borderRadius: 1,
                mb: 1,
                bgcolor: theme.palette.background.paper,
                '&:hover': {
                  bgcolor: theme.palette.action.hover
                }
              }}
              secondaryAction={
                <IconButton
                  edge="end"
                  aria-label="delete"
                  onClick={() => onDeleteDocument(doc.id)}
                  size="small"
                >
                  <DeleteIcon />
                </IconButton>
              }
            >
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <img src="/stacked-books.svg" alt="Document" width="16" height="16" />
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {doc.name}
                    </Typography>
                  </Box>
                }
                secondary={
                  <Box sx={{ mt: 0.5 }}>
                    <Chip
                      label={doc.type || 'Unknown'}
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                    />
                    <Typography variant="caption" display="block" color="text.secondary">
                      Size: {formatFileSize(doc.size)}
                    </Typography>
                    <Typography variant="caption" display="block" color="text.secondary">
                      Uploaded: {formatDate(doc.uploadTime)}
                    </Typography>
                  </Box>
                }
              />
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  );
};

export default DocumentsList; 