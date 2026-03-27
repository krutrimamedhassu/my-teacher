import React from 'react';
import { Box, Typography, Avatar, Button, TextField } from '@mui/material';
import { AccountCircle } from '@mui/icons-material';

const AccountSection = ({
  user,
  profileImageUrl,
  profileData,
  isEditingProfile,
  uploadingPicture,
  onProfileChange,
  onProfileSave,
  onStartEdit,
  onCancelEdit,
  onUploadPicture,
  onDeletePicture,
  saving
}) => {
  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
        Profile Information
      </Typography>

      {/* Profile Picture */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, mb: 3 }}>
        <Avatar
          src={profileImageUrl}
          sx={{
            width: 64,
            height: 64,
            bgcolor: '#666666',
            fontSize: '1.5rem',
            fontWeight: 600,
            color: '#ffffff'
          }}
        >
          {!user?.profile_image_url && (user?.full_name?.charAt(0) || user?.username?.charAt(0) || user?.email?.charAt(0) || <AccountCircle />)}
        </Avatar>
        <Box>
          <Typography variant="subtitle1" sx={{ fontWeight: 500, mb: 1 }}>
            Profile Picture
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              component="label"
              disabled={uploadingPicture}
              size="small"
            >
              {uploadingPicture ? 'Uploading...' : 'Upload'}
              <input
                type="file"
                hidden
                accept="image/*"
                onChange={onUploadPicture}
              />
            </Button>
            {user?.profile_image_url && (
              <Button
                variant="outlined"
                onClick={onDeletePicture}
                disabled={uploadingPicture}
                size="small"
                color="error"
              >
                Remove
              </Button>
            )}
          </Box>
        </Box>
      </Box>

      {/* Full Name */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 2, borderBottom: '1px solid #e0e0e0' }}>
        <Typography variant="body1" sx={{ fontWeight: 500 }}>
          Full Name
        </Typography>
        {!isEditingProfile ? (
          <Typography variant="body2" sx={{ color: '#666' }}>
            {profileData.fullName || 'Not set'}
          </Typography>
        ) : (
          <TextField
            name="fullName"
            value={profileData.fullName}
            onChange={onProfileChange}
            size="small"
            sx={{ minWidth: 200 }}
          />
        )}
      </Box>

      {/* Username */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 2, borderBottom: '1px solid #e0e0e0' }}>
        <Typography variant="body1" sx={{ fontWeight: 500 }}>
          Username
        </Typography>
        {!isEditingProfile ? (
          <Typography variant="body2" sx={{ color: '#666' }}>
            {profileData.username || 'Not set'}
          </Typography>
        ) : (
          <TextField
            name="username"
            value={profileData.username}
            onChange={onProfileChange}
            size="small"
            sx={{ minWidth: 200 }}
          />
        )}
      </Box>

      {/* Email */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 2, borderBottom: '1px solid #e0e0e0' }}>
        <Typography variant="body1" sx={{ fontWeight: 500 }}>
          Email
        </Typography>
        <Typography variant="body2" sx={{ color: '#666' }}>
          {user?.email || 'Not set'}
        </Typography>
      </Box>

      {/* Edit/Save Buttons */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 2 }}>
        <Typography variant="body1" sx={{ fontWeight: 500 }}>
          {isEditingProfile ? 'Save changes' : 'Edit profile'}
        </Typography>
        {!isEditingProfile ? (
          <Button
            variant="outlined"
            onClick={onStartEdit}
            size="small"
          >
            Edit
          </Button>
        ) : (
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="contained"
              onClick={onProfileSave}
              disabled={saving}
              size="small"
              sx={{ bgcolor: '#000', color: '#fff', '&:hover': { bgcolor: '#333' } }}
            >
              {saving ? 'Saving...' : 'Save'}
            </Button>
            <Button
              variant="outlined"
              onClick={onCancelEdit}
              size="small"
            >
              Cancel
            </Button>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default AccountSection;


