/**
 * Learning tools service
 * Contains all learning-related API functions
 */

import { apiRequest } from '../../utils/apiRequest';

// Breakdowns API
export const fetchBreakdown = async (content, subjectArea) => {
  const data = {
    content,
    subject_area: subjectArea
  };

  return apiRequest('/breakdowns/topic-breakdown/', 'POST', data);
};

// Key Concepts API
export const extractKeyConcepts = async (content, subjectArea) => {
  const data = {
    content,
    subject_area: subjectArea
  };

  return apiRequest('/key-concepts/extract-key-concepts', 'POST', data);
};

// QA API
export const askQuestion = async (question, documentId, context) => {
  const data = {
    question,
    document_id: documentId,
    context
  };

  return apiRequest('/qa', 'POST', data);
};

// Visuals API
export const generateVisual = async (content, subjectArea, visualType, focus) => {
  const data = {
    content,
    subject_area: subjectArea,
    visual_type: visualType,
    focus
  };

  return apiRequest('/visuals', 'POST', data);
};

// Speech API
export const textToSpeech = async (text, voiceType, speed, format) => {
  const data = {
    text,
    voice_type: voiceType,
    speed,
    format
  };

  return apiRequest('/speech', 'POST', data);
};

export const documentToSpeech = async (documentId, voiceType, speed, format) => {
  const queryParams = new URLSearchParams({
    document_id: documentId,
    voice_type: voiceType,
    speed,
    format
  }).toString();

  return apiRequest(`/speech/document?${queryParams}`, 'POST');
};

// Grades API
export const submitGrades = async (studentId, courseId, submissions, remainingAssignments, currentGrade) => {
  const data = {
    student_id: studentId,
    course_id: courseId,
    submissions,
    remaining_assignments: remainingAssignments,
    current_grade: currentGrade
  };

  return apiRequest('/grades', 'POST', data);
};