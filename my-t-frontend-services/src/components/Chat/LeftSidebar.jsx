import React, { useState, useEffect } from 'react';
import { Box, List, ListItem, ListItemText, ListItemButton, IconButton, Typography, Tooltip, Menu, MenuItem, Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, Avatar, Divider } from '@mui/material';
import { MoreVert as MoreVertIcon, Check as CheckIcon, Close as CloseIcon, Person as PersonIcon } from '@mui/icons-material';
import { Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { getConversationById } from '../../services';

const LeftSidebar = ({
  conversations,
  currentConversation,
  setCurrentConversation,
  createNewConversation,
  theme,
  open = true,
  onClose,
  onOpen,
  onSelectConversation,
  onEditConversation,
  onDeleteConversation,
  onProfileClick
}) => {
  const { isAuthenticated, user } = useAuth();
  console.log('📱 LeftSidebar: Component rendered with props:', {
    conversationsCount: conversations?.length || 0,
    currentConversation,
    open,
    isAuthenticated,
    user
  });
  
  // Helper function to get full image URL
  const getProfileImageUrl = (user) => {
    if (!user?.profile_image_url) return undefined;
    // If the URL already starts with http, return as is
    if (user.profile_image_url.startsWith('http')) {
      return user.profile_image_url;
    }
    // Otherwise, prepend the server URL from environment variable
    return `${process.env.REACT_APP_BASE_BACKEND_URL}${user.profile_image_url}`;
  };
  
  // State for menu and dialog
  const [menuAnchorEl, setMenuAnchorEl] = useState(null);
  const [menuConversationId, setMenuConversationId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editingValue, setEditingValue] = useState('');
  // Add state for delete confirmation dialog
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteConvTitle, setDeleteConvTitle] = useState('');
  const [deleteConversationId, setDeleteConversationId] = useState(null);
  // Search state
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState([]);

  // Deep search across conversation titles and message contents when dialog is open
  useEffect(() => {
    if (!searchOpen) return;
    const q = (searchQuery || '').trim().toLowerCase();
    if (!q) {
      setSearchResults([]);
      setSearching(false);
      return;
    }
    let cancelled = false;
    const run = async () => {
      setSearching(true);
      try {
        const convs = Array.isArray(conversations) ? conversations : [];
        const baseMatches = [];
        const toScan = [];
        for (const c of convs) {
          const title = (c?.title || '').toLowerCase();
          const preview = (c?.last_message_preview || '').toString().toLowerCase();
          if (title.includes(q)) {
            baseMatches.push({ id: c.id, title: c.title, snippet: c.last_message_preview || '' });
          } else if (preview.includes(q)) {
            baseMatches.push({ id: c.id, title: c.title, snippet: c.last_message_preview || '' });
          } else {
            toScan.push(c);
          }
        }
        // Limit deep scans for performance
        const scanLimit = Math.max(0, 25 - baseMatches.length);
        const scanTargets = toScan.slice(0, Math.min(scanLimit, toScan.length));
        const scanned = await Promise.allSettled(scanTargets.map(async (c) => {
          try {
            const data = await getConversationById(c.id);
            const msgs = Array.isArray(data?.messages) ? data.messages : [];
            for (const m of msgs) {
              const text = (m?.text || m?.content || '').toString();
              const lower = text.toLowerCase();
              const idx = lower.indexOf(q);
              if (idx !== -1) {
                // Build a simple snippet around the match
                const start = Math.max(0, idx - 40);
                const end = Math.min(text.length, idx + q.length + 40);
                const snippet = (start > 0 ? '…' : '') + text.slice(start, end) + (end < text.length ? '…' : '');
                return { id: c.id, title: c.title, snippet };
              }
            }
            return null;
          } catch (_) {
            return null;
          }
        }));
        if (cancelled) return;
        const deepMatches = scanned
          .map(r => (r.status === 'fulfilled' ? r.value : null))
          .filter(Boolean);
        const merged = [...baseMatches, ...deepMatches];
        const deduped = [];
        const seen = new Set();
        for (const item of merged) {
          if (item && !seen.has(item.id)) {
            seen.add(item.id);
            deduped.push(item);
          }
        }
        setSearchResults(deduped.slice(0, 25));
      } finally {
        if (!cancelled) setSearching(false);
      }
    };
    run();
    return () => { cancelled = true; };
  }, [searchOpen, searchQuery, conversations]);

  const handleMenuOpen = (event, conversation) => {
    console.log('📱 LeftSidebar: Menu opened for conversation:', conversation.id);
    setMenuAnchorEl(event.currentTarget);
    setMenuConversationId(conversation.id);
  };
  const handleMenuClose = () => {
    console.log('📱 LeftSidebar: Menu closed');
    setMenuAnchorEl(null);
    setMenuConversationId(null);
  };
  const handleRenameClick = () => {
    console.log('📱 LeftSidebar: Rename clicked for conversation:', menuConversationId);
    setEditingId(menuConversationId);
    const conv = conversations.find(c => c.id === menuConversationId);
    setEditingValue(conv?.title || '');
    handleMenuClose();
  };
  const handleRenameSaveInline = () => {
    console.log('📱 LeftSidebar: Rename save clicked for conversation:', editingId, 'new title:', editingValue.trim());
    if (onEditConversation && editingId && editingValue.trim()) {
      onEditConversation(editingId, editingValue.trim());
    }
    setEditingId(null);
    setEditingValue('');
  };
  const handleRenameCancelInline = () => {
    console.log('📱 LeftSidebar: Rename cancelled for conversation:', editingId);
    setEditingId(null);
    setEditingValue('');
  };
  const handleDeleteClick = () => {
    console.log('📱 LeftSidebar: Delete clicked for conversation:', menuConversationId);
    const conv = conversations.find(c => c.id === menuConversationId);
    setDeleteConvTitle(conv?.title || 'this conversation');
    setDeleteConversationId(menuConversationId);
    setDeleteDialogOpen(true);
    handleMenuClose();
  };
  const handleDeleteConfirm = () => {
    console.log('📱 LeftSidebar: Delete confirmed for conversation:', deleteConversationId);
    if (onDeleteConversation && deleteConversationId) {
      onDeleteConversation(deleteConversationId);
    }
    setDeleteDialogOpen(false);
    setDeleteConversationId(null);
  };
  const handleDeleteCancel = () => {
    console.log('📱 LeftSidebar: Delete cancelled for conversation:', deleteConversationId);
    setDeleteDialogOpen(false);
    setDeleteConversationId(null);
  };

  // No-op: clear empty action removed; handled automatically on refresh

  if (!open) {
    // Minimal open button/strip with navigation icons
    return (
      <Box
        sx={{
          width: 48,
          flexShrink: 0,
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          bgcolor: open ? '#f5f5f5' : 'white',
          borderRight: `1px solid ${theme.palette.divider}`,
          zIndex: 1201,
          pt: 2,
          gap: 1
        }}
      >
        {/* Header row: open button only */}
        <Box sx={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', pt: 1, mb: 2 }}>
          <Tooltip title="Open sidebar" placement="right">
            <IconButton 
              onClick={() => {
                console.log('📱 LeftSidebar: Open button clicked');
                onOpen();
              }} 
              size="small"
              sx={{
                width: 24,
                height: 24,
                borderRadius: '6px',
                color: theme.palette.text.secondary,
                '&:hover': {
                  bgcolor: theme.palette.action.hover,
                  transform: 'scale(1.05)',
                },
                transition: 'all 0.2s ease-in-out',
                fontSize: '14px',
                fontWeight: 'bold',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                minWidth: 'unset',
                padding: 0
              }}
            >
              <svg 
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 32 32"
                width="20" 
                height="20"
                fill="none" 
                stroke="#666666" 
                strokeWidth="3"
                strokeLinecap="round" 
                strokeLinejoin="round"
              >
                {/* outer rounded square */}
                <rect x="3" y="3" width="26" height="26" rx="4"/>
                {/* dividing bar on the left */}
                <line x1="13" y1="3" x2="13" y2="29"/>
              </svg>
            </IconButton>
          </Tooltip>
        </Box>
        
        {/* Sidebar actions */}
        <Tooltip title="New Chat" placement="right">
          <IconButton 
            onClick={() => {
              console.log('📱 LeftSidebar: New Chat button clicked');
              createNewConversation();
            }} 
            size="small"
            sx={{
              '&:hover': {
                bgcolor: theme.palette.action.hover,
              },
              '&:active': {
                bgcolor: 'transparent',
              },
              '&.Mui-focusVisible': {
                bgcolor: 'transparent',
              }
            }}
          >
            <img src="/pencil-chat.svg" alt="New Chat" width={24} height={24} />
          </IconButton>
        </Tooltip>
        
        <Tooltip title="Search Chats" placement="right">
          <IconButton 
            size="small"
            sx={{
              '&:hover': {
                bgcolor: theme.palette.action.hover,
              },
              '&:active': {
                bgcolor: 'transparent',
              },
              '&.Mui-focusVisible': {
                bgcolor: 'transparent',
              }
            }}
            onClick={() => {
              console.log('📱 LeftSidebar: Search (collapsed) clicked');
              setSearchOpen(true);
            }}
          >
            <img src="/search-chats.svg" alt="Search Chats" width={24} height={24} />
          </IconButton>
        </Tooltip>
        
        <Tooltip title="More Tools" placement="right">
          <IconButton 
            size="small"
            sx={{
              '&:hover': {
                bgcolor: theme.palette.action.hover,
              },
              '&:active': {
                bgcolor: 'transparent',
              },
              '&.Mui-focusVisible': {
                bgcolor: 'transparent',
              }
            }}
            component={RouterLink}
            to="/explore"
          >
            <img src="/more-tools.svg" alt="More GPT" width={24} height={24} />
          </IconButton>
                </Tooltip>
        
        {/* Search Dialog (collapsed view) */}
        <Dialog open={searchOpen} onClose={() => setSearchOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Search chats</DialogTitle>
          <DialogContent sx={{ pt: 1 }}>
            <TextField
              autoFocus
              fullWidth
              placeholder="Search titles and messages"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const first = (searchResults || [])[0];
                  if (first) {
                    if (onSelectConversation) onSelectConversation(first.id); else setCurrentConversation(first.id);
                    setSearchOpen(false);
                  }
                }
              }}
              variant="outlined"
            />
            <Box sx={{ mt: 1 }}>
              {searching && (
                <Typography variant="body2" sx={{ px: 2, py: 1, color: 'text.secondary' }}>Searching…</Typography>
              )}
              <List sx={{ maxHeight: 320, overflow: 'auto' }}>
                {(!searchQuery.trim()) && (
                  <ListItem>
                    <ListItemText primary="Start typing to search" secondary="Matches titles and message contents" />
                  </ListItem>
                )}
                {(searchQuery.trim() && searchResults.length === 0 && !searching) && (
                  <ListItem>
                    <ListItemText primary="No matches" secondary={`No titles or messages containing "${searchQuery}"`} />
                  </ListItem>
                )}
                {searchResults.map(conv => (
                  <ListItem disablePadding key={conv.id}>
                    <ListItemButton
                      onClick={() => {
                        if (onSelectConversation) onSelectConversation(conv.id); else setCurrentConversation(conv.id);
                        setSearchOpen(false);
                      }}
                    >
                      <ListItemText
                        primary={conv.title}
                        secondary={conv.snippet ? String(conv.snippet) : undefined}
                        primaryTypographyProps={{ noWrap: true }}
                        secondaryTypographyProps={{ noWrap: true }}
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setSearchOpen(false)}>Close</Button>
          </DialogActions>
        </Dialog>

        {/* Profile section for collapsed sidebar */}
        {isAuthenticated && (
          <>
            <Box sx={{ flexGrow: 1 }} /> {/* Spacer to push profile to bottom */}
            <Tooltip title={user?.full_name || user?.username || 'Profile'} placement="right">
              <IconButton
                onClick={onProfileClick}
                sx={{
                  '&:hover': {
                    bgcolor: theme.palette.action.hover,
                  },
                  '&:active': {
                    bgcolor: 'transparent',
                  },
                  '&.Mui-focusVisible': {
                    bgcolor: 'transparent',
                  },
                  mb: 1,
                }}
              >
                <Avatar
                  sx={{
                    width: 24,
                    height: 24,
                    bgcolor: theme.palette.primary.main,
                    fontSize: '12px',
                  }}
                  src={getProfileImageUrl(user)}
                >
                  {!user?.profile_image_url && (user?.full_name?.charAt(0) || user?.username?.charAt(0) || user?.email?.charAt(0) || <PersonIcon />)}
                </Avatar>
              </IconButton>
            </Tooltip>
          </>
        )}
        </Box>
    );
  }

  return (
    <Box
      sx={{
        width: 260,
        flexShrink: 0,
        height: '100vh',
        borderRight: `1px solid ${theme.palette.divider}`,
        display: 'flex',
        flexDirection: 'column',
        bgcolor: open ? '#f5f5f5' : 'white',
        position: 'relative'
      }}
    >
      {/* Header row: logo left, close button right */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 2.3, px: 2, mb: 2 }}>
        {/* Logo (favicon) */}
        <RouterLink to="/index" style={{ textDecoration: 'none', color: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <img src="/open-book.svg" alt="Logo" width="28" height="28" />
        </RouterLink>
        <Tooltip title="Close sidebar" placement="left">
          <IconButton 
            aria-label="close sidebar" 
            onClick={onClose} 
            size="small"
            sx={{
              width: 24,
              height: 24,
              borderRadius: '6px',
              color: theme.palette.text.secondary,
              '&:hover': {
                bgcolor: theme.palette.action.hover,
                transform: 'scale(1.05)',
              },
              transition: 'all 0.2s ease-in-out',
              fontSize: '14px',
              fontWeight: 'bold',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              minWidth: 'unset',
              padding: 0
            }}
          >
            <svg 
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 32 32"
              width="20" 
              height="20"
              fill="none" 
              stroke="#666666" 
              strokeWidth="3"
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              {/* outer rounded square */}
              <rect x="3" y="3" width="26" height="26" rx="4"/>
              {/* dividing bar on the left */}
              <line x1="13" y1="3" x2="13" y2="29"/>
            </svg>
          </IconButton>
        </Tooltip>
      </Box>

      {/* Top actions */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, p: 2, pt: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, width: '100%', cursor: 'pointer', py: 0.5, px: 1, borderRadius: 1, transition: 'background 0.2s', '&:hover': { bgcolor: theme.palette.action.hover } }} onClick={createNewConversation}>
          <img src="/pencil-chat.svg" alt="New Chat" width={24} height={24} />
          <Typography variant="body2" sx={{ fontWeight: 500 }}>New Chat</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, width: '100%', cursor: 'pointer', py: 0.5, px: 1, borderRadius: 1, transition: 'background 0.2s', '&:hover': { bgcolor: theme.palette.action.hover } }} onClick={() => { console.log('📱 LeftSidebar: Search clicked'); setSearchOpen(true); }}>
          <img src="/search-chats.svg" alt="Search Chats" width={24} height={24} />
          <Typography variant="body2" sx={{ fontWeight: 500 }}>Search Chats</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, width: '100%', cursor: 'pointer', py: 0.5, px: 1, borderRadius: 1, transition: 'background 0.2s', textDecoration: 'none', color: 'inherit', '&:hover': { bgcolor: theme.palette.action.hover, textDecoration: 'none' } }} component={RouterLink} to="/explore">
          <img src="/more-tools.svg" alt="More GPT" width={24} height={24} />
          <Typography variant="body2" sx={{ fontWeight: 500 }}>More GPT</Typography>
        </Box>
      </Box>

      {/* Spacing below top actions */}
      <Box sx={{ height: 16 }} />

      {/* Chats section header */}
      <Typography
        variant="caption"
        sx={{ color: theme.palette.text.secondary, px: 2, pt: 2, pb: 1, fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase' }}
      >
        Chats
      </Typography>

      {/* Inline search removed as requested */}

      {/* Chats list */}
      <Box sx={{
        flex: 1,
        overflowY: 'auto',
        overflowX: 'hidden',
        px: 0,
        // Hide scrollbars while keeping scroll functionality
        msOverflowStyle: 'none',
        scrollbarWidth: 'none',
        '&::-webkit-scrollbar': { display: 'none' }
      }}>
        <List>
          {(conversations || []).map((conversation) => (
            <ListItem
              key={conversation.id}
              onClick={() => onSelectConversation ? onSelectConversation(conversation.id) : setCurrentConversation(conversation.id)}
              sx={{
                borderRadius: 2,
                mx: 1,
                mb: 0.5,
                cursor: 'pointer',
                bgcolor: currentConversation === conversation.id ? theme.palette.action.selected : 'transparent',
                '&:hover': {
                  bgcolor: theme.palette.action.hover
                },
                position: 'relative',
                minHeight: 44
              }}
            >
              {editingId === conversation.id ? (
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                  <TextField
                    value={editingValue}
                    onChange={e => setEditingValue(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter' && editingValue.trim()) handleRenameSaveInline();
                      if (e.key === 'Escape') handleRenameCancelInline();
                    }}
                    autoFocus
                    size="small"
                    variant="standard"
                    fullWidth
                    InputProps={{ disableUnderline: true }}
                    sx={{
                      '& .MuiInputBase-input': { fontWeight: 500, fontSize: 15, py: 0.5 },
                      mr: 1,
                      '& .MuiInput-underline:before, & .MuiInput-underline:after': { borderBottom: 'none' },
                      '& .MuiInput-root:before, & .MuiInput-root:after': { borderBottom: 'none' },
                      '& .MuiInputBase-root': { borderBottom: 'none !important' }
                    }}
                  />
                  <IconButton size="small" onClick={handleRenameSaveInline} disabled={!editingValue.trim()}>
                    <CheckIcon fontSize="small" />
                  </IconButton>
                  <IconButton size="small" onClick={handleRenameCancelInline}>
                    <CloseIcon fontSize="small" />
                  </IconButton>
                </Box>
              ) : (
                <>
              <ListItemText
                primary={conversation.title}
                primaryTypographyProps={{
                  noWrap: true,
                  variant: 'body2',
                  fontWeight: 500
                }}
              />
                  <IconButton
                    size="small"
                    onClick={e => { e.stopPropagation(); handleMenuOpen(e, conversation); }}
                    sx={{ ml: 1 }}
                  >
                    <MoreVertIcon fontSize="small" />
                  </IconButton>
                </>
              )}
            </ListItem>
          ))}
          {((conversations || []).length === 0) && (
            <ListItem>
              <ListItemText primary="No chats found" />
            </ListItem>
          )}
        </List>
        <Menu
          anchorEl={menuAnchorEl}
          open={Boolean(menuAnchorEl)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={handleRenameClick}>Rename</MenuItem>
          <MenuItem onClick={handleDeleteClick}>Delete</MenuItem>
        </Menu>
        <Dialog open={deleteDialogOpen} onClose={handleDeleteCancel} maxWidth="xs" fullWidth>
          <DialogTitle sx={{ textAlign: 'center', pt: 4 }}>
            This will delete <b>{deleteConvTitle}</b>
          </DialogTitle>
          <DialogActions sx={{ justifyContent: 'center', pb: 4 }}>
            <Button onClick={handleDeleteCancel} variant="outlined">Cancel</Button>
            <Button onClick={handleDeleteConfirm} color="error" variant="contained">Delete</Button>
          </DialogActions>
                </Dialog>
        {/* Search Dialog */}
        <Dialog open={searchOpen} onClose={() => setSearchOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Search chats</DialogTitle>
          <DialogContent sx={{ pt: 1 }}>
            <TextField
              autoFocus
              fullWidth
              placeholder="Search titles and messages"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const first = (searchResults || [])[0];
                  if (first) {
                    if (onSelectConversation) onSelectConversation(first.id); else setCurrentConversation(first.id);
                    setSearchOpen(false);
                  }
                }
              }}
              variant="outlined"
            />
            <Box sx={{ mt: 1 }}>
              {searching && (
                <Typography variant="body2" sx={{ px: 2, py: 1, color: 'text.secondary' }}>Searching…</Typography>
              )}
              <List sx={{ maxHeight: 320, overflow: 'auto' }}>
                {(!searchQuery.trim()) && (
                  <ListItem>
                    <ListItemText primary="Start typing to search" secondary="Matches titles and message contents" />
                  </ListItem>
                )}
                {(searchQuery.trim() && searchResults.length === 0 && !searching) && (
                  <ListItem>
                    <ListItemText primary="No matches" secondary={`No titles or messages containing "${searchQuery}"`} />
                  </ListItem>
                )}
                {searchResults.map(conv => (
                  <ListItem disablePadding key={conv.id}>
                    <ListItemButton
                      onClick={() => {
                        if (onSelectConversation) onSelectConversation(conv.id); else setCurrentConversation(conv.id);
                        setSearchOpen(false);
                      }}
                    >
                      <ListItemText
                        primary={conv.title}
                        secondary={conv.snippet ? String(conv.snippet) : undefined}
                        primaryTypographyProps={{ noWrap: true }}
                        secondaryTypographyProps={{ noWrap: true }}
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setSearchOpen(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      </Box>
      
      {/* Profile Section */}
      {isAuthenticated && (
        <>
          <Divider sx={{ mx: 2 }} />
          <Box sx={{ p: 1 }}>
            <Box
              onClick={onProfileClick}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1.5,
                width: '100%',
                cursor: 'pointer',
                py: 0.5,
                px: 1,
                borderRadius: 2,
                textDecoration: 'none',
                color: 'inherit',
                transition: 'background 0.2s',
                '&:hover': {
                  bgcolor: theme.palette.action.hover,
                },
              }}
            >
              <Avatar
                sx={{
                  width: 32,
                  height: 32,
                  bgcolor: theme.palette.primary.main,
                  fontSize: '14px',
                }}
                src={getProfileImageUrl(user)} // Will use initials if no picture
              >
                {!user?.profile_image_url && (user?.full_name?.charAt(0) || user?.username?.charAt(0) || user?.email?.charAt(0) || <PersonIcon />)}
              </Avatar>
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: 500,
                    color: theme.palette.text.primary,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {user?.full_name || user?.username || 'User'}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    color: theme.palette.text.secondary,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    display: 'block',
                  }}
                >
                  {user?.email || 'View Profile'}
                </Typography>
              </Box>
            </Box>
          </Box>
        </>
      )}
      </Box>
  );
};

export default LeftSidebar;