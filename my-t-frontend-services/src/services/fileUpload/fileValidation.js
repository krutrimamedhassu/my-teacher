/**
 * File validation utilities
 * Contains file validation logic for uploads
 */

import { getSupportedTypes } from './documentService';

// Fallback constants in case API fails
export const FALLBACK_ALLOWED_FILE_TYPES = ['.pdf', '.docx', '.txt', '.html'];
export const FALLBACK_MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB in bytes

// Cache for API limits to avoid repeated requests
let cachedLimits = null;
let cacheTimestamp = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

// Get upload limits from API or cache
export const getUploadLimits = async () => {
  const now = Date.now();
  
  // Return cached limits if still valid
  if (cachedLimits && cacheTimestamp && (now - cacheTimestamp) < CACHE_DURATION) {
    return cachedLimits;
  }
  
  try {
    console.log('🔍 FileValidation: Fetching upload limits from API...');
    const response = await getSupportedTypes();
    
    if (response && response.limits) {
      cachedLimits = response.limits;
      cacheTimestamp = now;
      console.log('🔍 FileValidation: Upload limits cached:', cachedLimits);
      return cachedLimits;
    } else {
      throw new Error('Invalid API response structure');
    }
  } catch (error) {
    console.error('🔍 FileValidation: Failed to fetch upload limits, using fallbacks:', error);
    
    // Return fallback limits
    const fallbackLimits = {
      max_file_size: FALLBACK_MAX_FILE_SIZE,
      allowed_extensions: FALLBACK_ALLOWED_FILE_TYPES,
      allowed_mime_types: []
    };
    
    // Cache fallback limits temporarily
    cachedLimits = fallbackLimits;
    cacheTimestamp = now;
    
    return fallbackLimits;
  }
};

// Validate file type (async)
export const validateFileType = async (file) => {
  const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
  const limits = await getUploadLimits();
  return limits.allowed_extensions && limits.allowed_extensions.includes(fileExtension);
};

// Validate file size (async)  
export const validateFileSize = async (file) => {
  const limits = await getUploadLimits();
  const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
  
  // Use specific size limits based on file type
  if (fileExtension === '.pdf' && limits.max_pdf_size) {
    return file.size <= limits.max_pdf_size;
  } else if (['.jpg', '.jpeg', '.png', '.gif', '.webp', '.tiff', '.tif'].includes(fileExtension) && limits.max_image_size) {
    return file.size <= limits.max_image_size;
  } else {
    return file.size <= (limits.max_file_size || FALLBACK_MAX_FILE_SIZE);
  }
};

// Get file extension
export const getFileExtension = (filename) => {
  return '.' + filename.split('.').pop().toLowerCase();
};

// Format file size for display
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Comprehensive file validation (async)
export const validateFile = async (file) => {
  const errors = [];
  const limits = await getUploadLimits();
  
  // Validate file type
  const isValidType = await validateFileType(file);
  if (!isValidType) {
    const allowedTypes = limits.allowed_extensions || FALLBACK_ALLOWED_FILE_TYPES;
    errors.push(`File type not supported. Allowed types: ${allowedTypes.join(', ')}`);
  }
  
  // Validate file size
  const isValidSize = await validateFileSize(file);
  if (!isValidSize) {
    const fileExtension = getFileExtension(file.name);
    let sizeLimit;
    
    if (fileExtension === '.pdf' && limits.max_pdf_size) {
      sizeLimit = limits.max_pdf_size;
    } else if (['.jpg', '.jpeg', '.png', '.gif', '.webp', '.tiff', '.tif'].includes(fileExtension) && limits.max_image_size) {
      sizeLimit = limits.max_image_size;
    } else {
      sizeLimit = limits.max_file_size || FALLBACK_MAX_FILE_SIZE;
    }
    
    errors.push(`File size too large. Maximum size for ${fileExtension} files: ${formatFileSize(sizeLimit)}`);
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    limits // Return limits for reference
  };
};