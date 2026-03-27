import React, { useState } from 'react';
import { Box, Typography, Button, Card, Grid, CircularProgress, TextField, FormControlLabel, Switch, Alert, IconButton, InputAdornment } from '@mui/material';
import { ContentCopy, Visibility, VisibilityOff, Close } from '@mui/icons-material';

const ApiKeysSection = ({
  apiKeys,
  apiKeyUsage,
  tierInfo,
  loadingApiKeys,
  showCreate,
  onToggleCreate,
  newApiKeyData,
  setNewApiKeyData,
  onCreate,
  saving,
  editingKeyId,
  editApiKeyData,
  setEditApiKeyData,
  onEdit,
  onUpdate,
  onDelete,
  newlyCreatedApiKey,
  onDismissNewKey
}) => {
  const [showApiKey, setShowApiKey] = useState(true);
  const [copySuccess, setCopySuccess] = useState(false);

  const handleCopyApiKey = async () => {
    if (newlyCreatedApiKey?.api_key) {
      try {
        await navigator.clipboard.writeText(newlyCreatedApiKey.api_key);
        setCopySuccess(true);
        setTimeout(() => setCopySuccess(false), 2000);
      } catch (err) {
        console.error('Failed to copy: ', err);
      }
    }
  };
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          API Keys
        </Typography>
        <Button
          variant="contained"
          onClick={() => onToggleCreate((p) => !p)}
          size="small"
          sx={{ bgcolor: '#000', color: '#fff', '&:hover': { bgcolor: '#333' } }}
        >
          {showCreate ? 'Cancel' : 'Create New API Key'}
        </Button>
      </Box>

      {newlyCreatedApiKey && (
        <Alert 
          severity="success" 
          sx={{ mb: 3 }}
          action={
            <IconButton
              aria-label="close"
              color="inherit"
              size="small"
              onClick={onDismissNewKey}
            >
              <Close fontSize="inherit" />
            </IconButton>
          }
        >
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
            API Key Created Successfully!
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Please copy your API key now. You won't be able to see it again.
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <TextField
              value={showApiKey ? newlyCreatedApiKey.api_key : '••••••••••••••••••••••••••••••••••••••••••••••••••'}
              fullWidth
              size="small"
              InputProps={{
                readOnly: true,
                sx: { fontFamily: 'monospace', fontSize: '0.9rem' },
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle api key visibility"
                      onClick={() => setShowApiKey(!showApiKey)}
                      edge="end"
                      size="small"
                    >
                      {showApiKey ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                    <IconButton
                      aria-label="copy api key"
                      onClick={handleCopyApiKey}
                      edge="end"
                      size="small"
                      color={copySuccess ? "success" : "default"}
                    >
                      <ContentCopy />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Box>
          {copySuccess && (
            <Typography variant="caption" color="success.main">
              Copied to clipboard!
            </Typography>
          )}
          {newlyCreatedApiKey.key_info && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="caption" color="textSecondary">
                Key ID: {newlyCreatedApiKey.key_info.id} | 
                Name: {newlyCreatedApiKey.key_info.name} | 
                Created: {new Date(newlyCreatedApiKey.key_info.created_at).toLocaleString()}
              </Typography>
            </Box>
          )}
        </Alert>
      )}

      {showCreate && (
        <Card sx={{ mb: 3, p: 2 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
            New API Key
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            <TextField
              label="Name"
              size="small"
              value={newApiKeyData.name}
              onChange={(e) => setNewApiKeyData((prev) => ({ ...prev, name: e.target.value }))}
            />
            <TextField
              label="Description (Optional)"
              size="small"
              multiline
              rows={3}
              value={newApiKeyData.description}
              onChange={(e) => setNewApiKeyData((prev) => ({ ...prev, description: e.target.value }))}
            />
            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
              <Button
                variant="contained"
                onClick={onCreate}
                disabled={saving || !newApiKeyData.name.trim()}
                sx={{ bgcolor: '#000', color: '#fff', '&:hover': { bgcolor: '#333' } }}
              >
                {saving ? 'Creating...' : 'Create'}
              </Button>
              <Button 
                variant="outlined" 
                onClick={() => onToggleCreate(false)}
                sx={{
                  borderColor: '#999',
                  color: '#666',
                  '&:hover': {
                    borderColor: '#666',
                    backgroundColor: 'rgba(0, 0, 0, 0.04)'
                  }
                }}
              >
                Cancel
              </Button>
            </Box>
          </Box>
        </Card>
      )}

      {apiKeyUsage && (
        <Card sx={{ mb: 3, p: 2 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
            Usage Statistics
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="body2" color="textSecondary">
                Total Requests
              </Typography>
              <Typography variant="h6">{apiKeyUsage.total_requests || 0}</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" color="textSecondary">
                Active Keys
              </Typography>
              <Typography variant="h6">{apiKeyUsage.active_keys || 0}</Typography>
            </Grid>
          </Grid>
        </Card>
      )}

      {loadingApiKeys ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : apiKeys.length === 0 ? (
        <Card sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body1" color="textSecondary" sx={{ mb: 2 }}>
            No API keys found
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Create your first API key to get started
          </Typography>
        </Card>
      ) : (
        <Box>
          {apiKeys.map((apiKey) => (
            <Card key={apiKey.id} sx={{ mb: 2, p: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 2 }}>
                <Box sx={{ flex: 1 }}>
                  {editingKeyId === apiKey.id ? (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <TextField
                        label="Name"
                        size="small"
                        value={editApiKeyData.name}
                        onChange={(e) => setEditApiKeyData((prev) => ({ ...prev, name: e.target.value }))}
                      />
                      <TextField
                        label="Description"
                        size="small"
                        value={editApiKeyData.description}
                        onChange={(e) => setEditApiKeyData((prev) => ({ ...prev, description: e.target.value }))}
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={editApiKeyData.isActive}
                            onChange={(e) => setEditApiKeyData((prev) => ({ ...prev, isActive: e.target.checked }))}
                            sx={{
                              '& .MuiSwitch-switchBase.Mui-checked': {
                                color: '#000',
                                '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.08)' },
                              },
                              '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                                backgroundColor: '#000',
                              },
                            }}
                          />
                        }
                        label="Active"
                        sx={{ mt: 0.5 }}
                      />
                      <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                        <Button variant="contained" onClick={onUpdate} disabled={saving} sx={{ bgcolor: '#000', color: '#fff', '&:hover': { bgcolor: '#333' } }}>
                          {saving ? 'Saving...' : 'Save'}
                        </Button>
                        <Button 
                          variant="outlined" 
                          onClick={() => onEdit(null)}
                          sx={{
                            borderColor: '#999',
                            color: '#666',
                            '&:hover': {
                              borderColor: '#666',
                              backgroundColor: 'rgba(0, 0, 0, 0.04)'
                            }
                          }}
                        >
                          Cancel
                        </Button>
                      </Box>
                    </Box>
                  ) : (
                    <>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                          {apiKey.name}
                        </Typography>
                        <Box
                          sx={{
                            px: 1,
                            py: 0.5,
                            borderRadius: 1,
                            fontSize: '0.75rem',
                            bgcolor: apiKey.is_active ? '#e8f5e8' : '#ffeaea',
                            color: apiKey.is_active ? '#2e7d32' : '#d32f2f'
                          }}
                        >
                          {apiKey.is_active ? 'Active' : 'Inactive'}
                        </Box>
                      </Box>
                      {apiKey.description && (
                        <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                          {apiKey.description}
                        </Typography>
                      )}
                      <Typography variant="caption" color="textSecondary">
                        Created: {new Date(apiKey.created_at).toLocaleDateString()}
                      </Typography>
                      {apiKey.last_used && (
                        <Typography variant="caption" color="textSecondary" sx={{ ml: 2 }}>
                          Last used: {new Date(apiKey.last_used).toLocaleDateString()}
                        </Typography>
                      )}
                    </>
                  )}
                </Box>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  {editingKeyId === apiKey.id ? null : (
                    <Button 
                      variant="outlined" 
                      size="small" 
                      onClick={() => onEdit(apiKey)}
                      sx={{
                        borderColor: '#999',
                        color: '#666',
                        '&:hover': {
                          borderColor: '#666',
                          backgroundColor: 'rgba(0, 0, 0, 0.04)'
                        }
                      }}
                    >
                      Edit
                    </Button>
                  )}
                  <Button 
                    variant="outlined" 
                    color="error" 
                    size="small" 
                    onClick={() => onDelete(apiKey.id)}
                    sx={{
                      borderColor: '#d32f2f',
                      color: '#d32f2f',
                      '&:hover': {
                        borderColor: '#b71c1c',
                        backgroundColor: 'rgba(211, 47, 47, 0.04)'
                      }
                    }}
                  >
                    Delete
                  </Button>
                </Box>
              </Box>
            </Card>
          ))}
        </Box>
      )}

      {tierInfo && (
        <Card sx={{ mt: 3, p: 2 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
            Tier Information
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Current tier: {tierInfo.tier || 'free'}
          </Typography>
          {tierInfo.limits && (
            <>
              <Typography variant="body2" color="textSecondary">
                Monthly limit: {tierInfo.limits.monthly_limit === -1 ? 'Unlimited' : tierInfo.limits.monthly_limit}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Daily limit: {tierInfo.limits.daily_limit === -1 ? 'Unlimited' : tierInfo.limits.daily_limit}
              </Typography>
            </>
          )}
        </Card>
      )}
    </Box>
  );
};

export default ApiKeysSection;


