import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Alert,
  Modal,
  CircularProgress,
  IconButton,
  Backdrop
} from '@mui/material';
import {
  Close
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { getCurrentUser, updateProfile, updatePassword, updateEmail, logout, uploadProfilePicture, deleteProfilePicture, createApiKey, getUserApiKeys, updateApiKey, deleteApiKey, getApiKeyUsage, getTierInformation } from '../services';
import { useAuth } from '../contexts/AuthContext';
import { useSettings } from '../contexts/SettingsContext';
import { useApiKey } from '../contexts/ApiKeyContext';
import AccountSection from './profile/AccountSection';
import GeneralSection from './profile/GeneralSection';
import SecuritySection from './profile/SecuritySection';
import ApiKeysSection from './profile/ApiKeysSection';
import ChangePasswordDialog from './profile/ChangePasswordDialog';
import ChangeEmailDialog from './profile/ChangeEmailDialog';

const ProfilePage = ({ onClose: externalOnClose }) => {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const { settings, updateSettings } = useSettings();
  const { refreshApiKeys } = useApiKey();

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

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Profile form state
  const [profileData, setProfileData] = useState({
    fullName: '',
    username: ''
  });
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  
  // Password change state
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false
  });
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  
  // Email change state
  const [emailData, setEmailData] = useState({
    currentPassword: '',
    newEmail: ''
  });
  const [showEmailPassword, setShowEmailPassword] = useState(false);
  const [showEmailDialog, setShowEmailDialog] = useState(false);

  // Profile picture state
  const [uploadingPicture, setUploadingPicture] = useState(false);

  // API Key management state
  const [apiKeys, setApiKeys] = useState([]);
  const [apiKeyUsage, setApiKeyUsage] = useState(null);
  const [tierInfo, setTierInfo] = useState(null);
  const [loadingApiKeys, setLoadingApiKeys] = useState(false);
  const [showCreateApiKeyInline, setShowCreateApiKeyInline] = useState(false);
  const [editingKeyId, setEditingKeyId] = useState(null);
  const [newApiKeyData, setNewApiKeyData] = useState({
    name: '',
    description: ''
  });
  const [editApiKeyData, setEditApiKeyData] = useState({
    name: '',
    description: '',
    isActive: true
  });
  const [newlyCreatedApiKey, setNewlyCreatedApiKey] = useState(null);

  // Modal and tab state
  const [open, setOpen] = useState(true); // Open by default when component mounts
  const [currentTab, setCurrentTab] = useState(0);

  const fetchUserData = useCallback(async () => {
    try {
      const userData = await getCurrentUser();
      setUser(userData);
      setProfileData({
        fullName: userData.full_name || '',
        username: userData.username || ''
      });
    } catch (error) {
      console.error('Error fetching user data:', error);
      // Redirect to login on any authentication error
      navigate('/login');
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    fetchUserData();
  }, [fetchUserData]);

  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfileData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleProfileSave = async () => {
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      await updateProfile(profileData);
      setSuccess('Profile updated successfully!');
      setIsEditingProfile(false);
      await fetchUserData(); // Refresh user data
      await refreshUser(); // Refresh auth context
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSuccess('');
      }, 3000);
    } catch (error) {
      console.error('Error updating profile:', error);
      setError(error.message || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleProfilePictureUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setError('Please upload a valid image file (JPG, PNG, GIF, or WebP)');
      return;
    }

    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
      setError('Image size must be less than 10MB');
      return;
    }

    setUploadingPicture(true);
    setError('');
    setSuccess('');

    try {
      const response = await uploadProfilePicture(file);
      setSuccess(response.message || 'Profile picture updated successfully!');
      await fetchUserData(); // Refresh user data
      await refreshUser(); // Refresh auth context
    } catch (error) {
      console.error('Error uploading profile picture:', error);
      setError(error.message || 'Failed to upload profile picture');
    } finally {
      setUploadingPicture(false);
    }
  };

  const handleProfilePictureDelete = async () => {
    setUploadingPicture(true);
    setError('');
    setSuccess('');

    try {
      await deleteProfilePicture();
      setSuccess('Profile picture removed successfully!');
      await fetchUserData(); // Refresh user data
      await refreshUser(); // Refresh auth context
    } catch (error) {
      console.error('Error deleting profile picture:', error);
      setError(error.message || 'Failed to remove profile picture');
    } finally {
      setUploadingPicture(false);
    }
  };

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handlePasswordSave = async () => {
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    if (passwordData.newPassword.length < 8) {
      setError('New password must be at least 8 characters long');
      return;
    }

    setSaving(true);
    setError('');
    setSuccess('');

    try {
      await updatePassword(passwordData.currentPassword, passwordData.newPassword);
      setSuccess('Password updated successfully!');
      setShowPasswordDialog(false);
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
    } catch (error) {
      console.error('Error updating password:', error);
      setError(error.message || 'Failed to update password');
    } finally {
      setSaving(false);
    }
  };

  const handleEmailChange = (e) => {
    const { name, value } = e.target;
    setEmailData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleEmailSave = async () => {
    if (!emailData.newEmail.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    setSaving(true);
    setError('');
    setSuccess('');

    try {
      await updateEmail(emailData.currentPassword, emailData.newEmail);
      setSuccess('Email updated successfully!');
      setShowEmailDialog(false);
      setEmailData({
        currentPassword: '',
        newEmail: ''
      });
      await fetchUserData(); // Refresh user data
    } catch (error) {
      console.error('Error updating email:', error);
      setError(error.message || 'Failed to update email');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // API Key Management Functions
  const fetchApiKeys = async () => {
    setLoadingApiKeys(true);
    try {
      const keys = await getUserApiKeys();
      setApiKeys(keys);
    } catch (error) {
      console.error('Error fetching API keys:', error);
      setError('Failed to fetch API keys');
    } finally {
      setLoadingApiKeys(false);
    }
  };

  const fetchApiKeyUsage = async () => {
    try {
      const usage = await getApiKeyUsage();
      setApiKeyUsage(usage);
    } catch (error) {
      console.error('Error fetching API key usage:', error);
    }
  };

  const fetchTierInfo = async () => {
    try {
      const tiers = await getTierInformation();
      setTierInfo(tiers);
    } catch (error) {
      console.error('Error fetching tier information:', error);
    }
  };

  const handleCreateApiKey = async () => {
    if (!newApiKeyData.name.trim()) {
      setError('API key name is required');
      return;
    }

    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const response = await createApiKey(newApiKeyData.name, newApiKeyData.description);
      setNewlyCreatedApiKey(response);
      setSuccess('API key created successfully! Make sure to copy it now as you won\'t be able to see it again.');
      setShowCreateApiKeyInline(false);
      setNewApiKeyData({ name: '', description: '' });
      await fetchApiKeys();
      refreshApiKeys(); // Refresh the API key context
    } catch (error) {
      console.error('Error creating API key:', error);
      setError(error.message || 'Failed to create API key');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateApiKey = async () => {
    if (!editApiKeyData.name.trim()) {
      setError('API key name is required');
      return;
    }

    setSaving(true);
    setError('');
    setSuccess('');

    try {
      await updateApiKey(editingKeyId, editApiKeyData);
      setSuccess('API key updated successfully!');
      setEditingKeyId(null);
      setEditApiKeyData({ name: '', description: '', isActive: true });
      await fetchApiKeys();
      refreshApiKeys(); // Refresh the API key context
    } catch (error) {
      console.error('Error updating API key:', error);
      setError(error.message || 'Failed to update API key');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteApiKey = async (keyId) => {
    if (!window.confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
      return;
    }

    setSaving(true);
    setError('');
    setSuccess('');

    try {
      await deleteApiKey(keyId);
      setSuccess('API key deleted successfully!');
      await fetchApiKeys();
      refreshApiKeys(); // Refresh the API key context
    } catch (error) {
      console.error('Error deleting API key:', error);
      setError(error.message || 'Failed to delete API key');
    } finally {
      setSaving(false);
    }
  };

  const handleEditApiKey = (apiKey) => {
    setEditingKeyId(apiKey.id);
    setEditApiKeyData({
      name: apiKey.name || '',
      description: apiKey.description || '',
      isActive: apiKey.is_active !== false
    });
  };

  // Load API key data when tab changes to API Keys
  useEffect(() => {
    if (currentTab === 3) {
      fetchApiKeys();
      fetchApiKeyUsage();
      fetchTierInfo();
    }
  }, [currentTab]);

  const handleClose = () => {
    setOpen(false);
    if (externalOnClose) {
      externalOnClose();
    } else {
      navigate(-1); // Go back to previous page
    }
  };

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
    // Clear success and error messages when switching tabs
    setSuccess('');
    setError('');
  };

  const handleChatSettingChange = (setting, value) => {
    updateSettings({
      ...settings,
      [setting]: value
    });
  };

  const togglePasswordVisibility = (field) => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#f8f8f8',
          fontFamily: 'Times New Roman, serif',
        }}
      >
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <>
      <Modal
        open={open}
        onClose={handleClose}
        closeAfterTransition
        slots={{ backdrop: Backdrop }}
        slotProps={{
          backdrop: {
            timeout: 500,
            sx: {
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
            }
          }
        }}
      >
              <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 680,
            height: 553,
            bgcolor: '#ffffff',
            borderRadius: 2,
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
        {/* Main Content Area with Sidebar */}
        <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {/* Left Sidebar with Header */}
          <Box sx={{
            width: 220,
            borderRight: '1px solid #e0e0e0',
            bgcolor: '#f5f5f5',
            overflow: 'auto',
            display: 'flex',
            flexDirection: 'column'
          }}>
            {/* Header area for left side */}
            <Box sx={{ p: 2 }}>
              <IconButton onClick={handleClose} size="small">
                <Close />
              </IconButton>
            </Box>
            <Box sx={{ p: 2 }}>
              {[
                { label: 'Account', value: 0 },
                { label: 'General', value: 1 },
                { label: 'Security', value: 2 },
                { label: 'API Keys', value: 3 },
              ].map((item) => (
                <Box
                  key={item.value}
                  onClick={() => handleTabChange(null, item.value)}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    p: 1,
                    borderRadius: 1,
                    cursor: 'pointer',
                    bgcolor: currentTab === item.value ? '#e0e0e0' : 'transparent',
                    color: currentTab === item.value ? '#000' : '#666',
                    '&:hover': {
                      bgcolor: currentTab === item.value ? '#e0e0e0' : '#eeeeee',
                    },
                    mb: 0.3,
                  }}
                >
                  <Typography variant="body2" sx={{ fontWeight: currentTab === item.value ? 600 : 400, fontSize: '13px' }}>
                    {item.label}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Box>

          {/* Right Content Area */}
          <Box sx={{ flex: 1, overflow: 'hidden', borderRight: '1px solid #e0e0e0', display: 'flex', flexDirection: 'column' }}>
            {/* Header with title */}
            <Box sx={{ p: 3, borderBottom: '1px solid #e0e0e0' }}>
              <Typography variant="h5" sx={{ fontWeight: 600, color: '#000' }}>
                {currentTab === 0 && 'Account'}
                {currentTab === 1 && 'General Settings'}
                {currentTab === 2 && 'Security'}
                {currentTab === 3 && 'API Keys'}
              </Typography>
            </Box>
            {/* Content area */}
            <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
          {/* Error/Success Messages */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
          {success && (
            <Alert severity="success" sx={{ mb: 3 }}>
              {success}
            </Alert>
          )}

            {/* Tab Content */}
            {currentTab === 1 && (
              <GeneralSection
                streamingMode={settings.streamingMode || 'traditional'}
                showRightSidebar={settings.showRightSidebar !== false}
                onChangeSetting={handleChatSettingChange}
              />
            )}

            {currentTab === 2 && (
              <SecuritySection
                onOpenPassword={() => setShowPasswordDialog(true)}
                onOpenEmail={() => setShowEmailDialog(true)}
                onLogout={handleLogout}
              />
            )}

            {currentTab === 3 && (
              <ApiKeysSection
                apiKeys={apiKeys}
                apiKeyUsage={apiKeyUsage}
                tierInfo={tierInfo}
                loadingApiKeys={loadingApiKeys}
                showCreate={showCreateApiKeyInline}
                onToggleCreate={(val) => typeof val === 'function' ? setShowCreateApiKeyInline(val) : setShowCreateApiKeyInline(val)}
                newApiKeyData={newApiKeyData}
                setNewApiKeyData={setNewApiKeyData}
                onCreate={handleCreateApiKey}
                saving={saving}
                editingKeyId={editingKeyId}
                editApiKeyData={editApiKeyData}
                setEditApiKeyData={setEditApiKeyData}
                onEdit={(apiKey) => {
                  if (!apiKey) {
                    setEditingKeyId(null);
                    setEditApiKeyData({ name: '', description: '', isActive: true });
                  } else {
                    handleEditApiKey(apiKey);
                  }
                }}
                onUpdate={handleUpdateApiKey}
                onDelete={handleDeleteApiKey}
                newlyCreatedApiKey={newlyCreatedApiKey}
                onDismissNewKey={() => setNewlyCreatedApiKey(null)}
              />
            )}

            {currentTab === 0 && (
              <AccountSection
                user={user}
                profileImageUrl={getProfileImageUrl(user)}
                profileData={profileData}
                isEditingProfile={isEditingProfile}
                uploadingPicture={uploadingPicture}
                onProfileChange={handleProfileChange}
                onProfileSave={handleProfileSave}
                onStartEdit={() => setIsEditingProfile(true)}
                onCancelEdit={() => {
                            setIsEditingProfile(false);
                            setProfileData({
                              fullName: user?.full_name || '',
                              username: user?.username || ''
                            });
                          }}
                onUploadPicture={handleProfilePictureUpload}
                onDeletePicture={handleProfilePictureDelete}
                saving={saving}
              />
            )}
            </Box>
          </Box>
        </Box>
      </Box>
      </Modal>

        <ChangePasswordDialog
          open={showPasswordDialog}
          onClose={() => setShowPasswordDialog(false)}
          onToggleVisibility={togglePasswordVisibility}
          showPasswords={showPasswords}
          passwordData={passwordData}
              onChange={handlePasswordChange}
          onSave={handlePasswordSave}
          saving={saving}
        />

        <ChangeEmailDialog
          open={showEmailDialog}
          onClose={() => setShowEmailDialog(false)}
          showEmailPassword={showEmailPassword}
          toggleShowPassword={() => setShowEmailPassword(!showEmailPassword)}
          emailData={emailData}
              onChange={handleEmailChange}
          onSave={handleEmailSave}
          saving={saving}
        />

        {/* Inline API key creation is rendered within the API Keys tab */}
    </>
  );
};

export default ProfilePage; 