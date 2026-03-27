/**
 * Speech service for Speech-to-Text (STT) and Text-to-Speech (TTS)
 */

import { apiRequest, TokenManager } from '../../utils/apiRequest';

/**
 * Send audio file to backend for transcription (Speech-to-Text)
 * @param {Blob} audioBlob - Audio recording as Blob
 * @returns {Promise<{text: string}>} - Transcribed text
 */
export const sendAudioForTranscription = async (audioBlob) => {
  console.log('🎤 speechService: Sending audio for transcription, size:', audioBlob.size);

  try {
    // Create FormData and append audio file
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');

    console.log('🎤 speechService: FormData created with audio file');

    // Send to backend STT endpoint
    const response = await apiRequest('/speech/stt', 'POST', formData, true);

    console.log('🎤 speechService: STT response received:', response);

    if (response && response.text) {
      return response;
    } else {
      throw new Error('Invalid response from STT endpoint');
    }
  } catch (error) {
    console.error('❌ speechService: STT error:', error);
    throw error;
  }
};

/**
 * Convert text to speech using backend TTS endpoint
 * @param {string} text - Text to convert to speech
 * @param {string} voice - Voice to use (alloy, echo, fable, onyx, nova, shimmer)
 * @returns {Promise<Blob>} - Audio blob (MP3)
 */
export const convertTextToSpeech = async (text, voice = 'alloy') => {
  console.log('🔊 speechService: Converting text to speech, length:', text.length, 'voice:', voice);

  try {
    // Prepare request body
    const data = {
      text: text,
      voice: voice
    };

    // Get the API URL
    const API_BASE_URL = process.env.NODE_ENV === 'production'
      ? `${process.env.REACT_APP_BASE_BACKEND_URL}/api/v1`
      : '/api/v1';

    const url = `${API_BASE_URL}/speech/tts`;

    // Refresh token if access token is missing or expired but a refresh token exists
    if (TokenManager.getRefreshToken() && (!TokenManager.isAuthenticated() || TokenManager.isAccessTokenExpired())) {
      try {
        await TokenManager.refreshAccessToken();
      } catch (_) {}
    }

    // Get auth token
    const token = TokenManager.getAccessToken();
    const headers = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    console.log('🔊 speechService: Sending TTS request to:', url);

    // Make fetch request
    const response = await fetch(url, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(data),
      credentials: 'include'
    });

    console.log('🔊 speechService: TTS response status:', response.status);

    if (!response.ok) {
      throw new Error(`TTS request failed with status ${response.status}`);
    }

    // Get audio blob
    const audioBlob = await response.blob();
    console.log('🔊 speechService: Audio blob received, size:', audioBlob.size);

    return audioBlob;
  } catch (error) {
    console.error('❌ speechService: TTS error:', error);
    throw error;
  }
};

/**
 * Convert text to speech using streaming endpoint (FASTER - 3-5s for long text)
 * @param {string} text - Text to convert to speech
 * @param {string} voice - Voice to use (optional, uses backend default)
 * @returns {Promise<Blob>} - Complete audio blob (MP3)
 */
export const convertTextToSpeechStreaming = async (text, voice = 'alloy') => {
  console.log('🔊 speechService: Converting text to speech (STREAMING), length:', text.length, 'voice:', voice);

  try {
    // Get the API URL
    const API_BASE_URL = process.env.NODE_ENV === 'production'
      ? `${process.env.REACT_APP_BASE_BACKEND_URL}/api/v1`
      : '/api/v1';

    const url = `${API_BASE_URL}/speech/tts/stream`;

    // Refresh token if access token is missing or expired but a refresh token exists
    if (TokenManager.getRefreshToken() && (!TokenManager.isAuthenticated() || TokenManager.isAccessTokenExpired())) {
      try {
        await TokenManager.refreshAccessToken();
      } catch (_) {}
    }

    // Get auth token
    const token = TokenManager.getAccessToken();
    const headers = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    console.log('🔊 speechService: Sending streaming TTS request to:', url);

    // Make fetch request
    const response = await fetch(url, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({ text, voice }),
      credentials: 'include'
    });

    console.log('🔊 speechService: Streaming TTS response status:', response.status);

    if (!response.ok) {
      throw new Error(`Streaming TTS request failed with status ${response.status}`);
    }

    // Read the stream and collect chunks
    const reader = response.body.getReader();
    const chunks = [];

    console.log('🔊 speechService: Reading audio stream...');

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        console.log('🔊 speechService: Stream complete, total chunks:', chunks.length);
        break;
      }

      chunks.push(value);

      // Log progress for first few chunks
      if (chunks.length <= 3) {
        console.log(`🔊 speechService: Received chunk ${chunks.length}, size: ${value.length} bytes`);
      }
    }

    // Combine all chunks into single blob
    const audioBlob = new Blob(chunks, { type: 'audio/mpeg' });
    console.log('🔊 speechService: Audio blob created, total size:', audioBlob.size);

    return audioBlob;
  } catch (error) {
    console.error('❌ speechService: Streaming TTS error:', error);
    throw error;
  }
};

/**
 * Play audio from blob
 * @param {Blob} audioBlob - Audio blob to play
 * @returns {Promise<void>} - Resolves when audio finishes playing
 */
export const playAudioFromBlob = async (audioBlob) => {
  return new Promise((resolve, reject) => {
    try {
      console.log('🔊 speechService: Creating audio URL from blob');

      // Create object URL from blob
      const audioUrl = URL.createObjectURL(audioBlob);

      // Create audio element
      const audio = new Audio(audioUrl);

      // Add event listeners
      audio.onended = () => {
        console.log('🔊 speechService: Audio playback finished');
        URL.revokeObjectURL(audioUrl);
        resolve();
      };

      audio.onerror = (error) => {
        console.error('❌ speechService: Audio playback error:', error);
        URL.revokeObjectURL(audioUrl);
        reject(error);
      };

      // Play audio
      console.log('🔊 speechService: Starting audio playback');
      audio.play().catch(error => {
        console.error('❌ speechService: Failed to play audio:', error);
        URL.revokeObjectURL(audioUrl);
        reject(error);
      });
    } catch (error) {
      console.error('❌ speechService: Error creating audio:', error);
      reject(error);
    }
  });
};

/**
 * Check if browser supports audio recording
 * @returns {boolean} - True if MediaRecorder is supported
 */
export const isRecordingSupported = () => {
  return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
};

/**
 * Request microphone permission and start recording
 * @returns {Promise<{mediaRecorder: MediaRecorder, stream: MediaStream}>}
 */
export const startRecording = async () => {
  console.log('🎤 speechService: Starting recording...');

  if (!isRecordingSupported()) {
    throw new Error('Audio recording is not supported in this browser');
  }

  try {
    // Request microphone access
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    console.log('🎤 speechService: Microphone access granted');

    // Create MediaRecorder
    const mediaRecorder = new MediaRecorder(stream);
    console.log('🎤 speechService: MediaRecorder created');

    return { mediaRecorder, stream };
  } catch (error) {
    console.error('❌ speechService: Failed to start recording:', error);
    throw error;
  }
};

/**
 * Stop all tracks in a media stream
 * @param {MediaStream} stream - Media stream to stop
 */
export const stopStream = (stream) => {
  if (stream) {
    stream.getTracks().forEach(track => {
      track.stop();
      console.log('🎤 speechService: Stopped media track');
    });
  }
};
