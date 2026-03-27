import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Alert,
  Divider
} from '@mui/material';

const QAPairs = ({ qaData, theme }) => {
  const [userAnswers, setUserAnswers] = useState({});
  const [isSubmitted, setIsSubmitted] = useState(false);

  // Reset state when new QA data is loaded
  useEffect(() => {
    setUserAnswers({});
    setIsSubmitted(false);
  }, [qaData]);

  const handleAnswerChange = (questionIndex, answer) => {
    if (!isSubmitted) {
      setUserAnswers(prev => ({
        ...prev,
        [questionIndex]: answer
      }));
    }
  };

  const handleSubmit = () => {
    const answeredCount = Object.keys(userAnswers).length;
    const totalQuestions = qaData.qa_pairs.length;
    
    if (answeredCount < totalQuestions) {
      alert(`Please answer all ${totalQuestions} questions before submitting.`);
      return;
    }

    setIsSubmitted(true);
  };

  const renderQA = (qa, index) => {
    const userAnswer = userAnswers[index];

    return (
      <Box key={index} sx={{ mb: 5 }}>
        {/* Question Text */}
        <Typography 
          variant="body1" 
          sx={{ 
            mb: 4, 
            fontWeight: 500,
            color: theme.palette.text.primary,
            fontSize: '1.2rem',
            lineHeight: 1.7,
            fontFamily: 'Times New Roman, serif'
          }}
        >
          {index + 1}. {qa.question}
        </Typography>

        {/* Answer Space */}
        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            multiline
            rows={6}
            variant="outlined"
            placeholder="Write your answer in the space provided below..."
            value={userAnswer || ''}
            onChange={(e) => handleAnswerChange(index, e.target.value)}
            disabled={isSubmitted}
            sx={{
              '& .MuiOutlinedInput-root': {
                border: `2px solid ${theme.palette.divider}`,
                borderRadius: 0,
                backgroundColor: theme.palette.background.paper,
                '& fieldset': {
                  border: 'none'
                },
                '&:hover fieldset': {
                  border: 'none'
                },
                '&.Mui-focused fieldset': {
                  border: 'none'
                }
              },
              '& .MuiInputBase-input': {
                fontFamily: 'Times New Roman, serif',
                fontSize: '1.1rem',
                color: theme.palette.text.primary,
                lineHeight: 1.6
              }
            }}
          />
        </Box>

        {/* Actual Answer */}
        {isSubmitted && (
          <Box sx={{ 
            mt: 4, 
            p: 4, 
            backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.05)' : '#f8f8f8', 
            border: `2px solid ${theme.palette.divider}`,
            borderRadius: 0
          }}>
            <Typography 
              variant="h6" 
              sx={{ 
                fontWeight: 700, 
                mb: 3, 
                color: theme.palette.text.primary,
                fontSize: '1.2rem',
                fontFamily: 'Times New Roman, serif',
                borderBottom: `2px solid ${theme.palette.divider}`,
                pb: 2
              }}
            >
              Correct Answer:
            </Typography>
            <Typography 
              variant="body1" 
              sx={{
                color: theme.palette.text.primary,
                fontFamily: 'Times New Roman, serif',
                lineHeight: 1.7,
                fontSize: '1.1rem'
              }}
            >
              {qa.answer}
            </Typography>
          </Box>
        )}
      </Box>
    );
  };

  const answeredCount = Object.keys(userAnswers).length;
  const totalQuestions = qaData.qa_pairs.length;

  return (
    <Box sx={{ p: 3 }}>
      {/* Question Paper Header */}
      <Paper 
        elevation={0} 
        sx={{ 
          mb: 4, 
          p: 4, 
          border: `3px solid ${theme.palette.divider}`,
          borderRadius: 0,
          backgroundColor: theme.palette.background.paper
        }}
      >
        <Typography 
          variant="h3" 
          sx={{ 
            fontWeight: 700, 
            textAlign: 'center',
            color: theme.palette.text.primary,
            fontFamily: 'Times New Roman, serif',
            mb: 2,
            fontSize: '2.2rem'
          }}
        >
          QUESTION PAPER
        </Typography>
        <Typography 
          variant="h5" 
          sx={{ 
            textAlign: 'center',
            color: theme.palette.text.primary,
            fontFamily: 'Times New Roman, serif',
            mb: 3,
            fontSize: '1.4rem'
          }}
        >
          Total Questions: {totalQuestions}
        </Typography>
        <Divider sx={{ borderColor: theme.palette.divider, borderWidth: 3, mb: 3 }} />
        
        {!isSubmitted && (
          <Typography 
            variant="h6" 
            sx={{ 
              textAlign: 'center',
              color: theme.palette.text.primary,
              fontFamily: 'Times New Roman, serif',
              fontStyle: 'italic',
              fontSize: '1.1rem'
            }}
          >
            Instructions: Answer all questions in the space provided. Click Submit when finished.
          </Typography>
        )}
      </Paper>

      {!isSubmitted && (
        <Box sx={{ mb: 4 }}>
          <Alert 
            severity="info" 
            sx={{ 
              mb: 3,
              border: `2px solid ${theme.palette.divider}`,
              borderRadius: 0,
              backgroundColor: theme.palette.mode === 'dark' ? 'rgba(33,150,243,0.1)' : '#f0f8ff',
              '& .MuiAlert-message': {
                fontSize: '1.1rem',
                fontFamily: 'Times New Roman, serif',
                color: theme.palette.text.primary
              }
            }}
          >
            Progress: {answeredCount} out of {totalQuestions} questions answered
          </Alert>
        </Box>
      )}

      {isSubmitted && (
        <Box sx={{ 
          mb: 4, 
          p: 4, 
          backgroundColor: theme.palette.mode === 'dark' ? 'rgba(76,175,80,0.1)' : '#f8fff8', 
          border: `2px solid ${theme.palette.divider}`,
          borderRadius: 0
        }}>
          <Typography 
            variant="h5" 
            sx={{ 
              fontWeight: 700, 
              color: theme.palette.text.primary,
              fontFamily: 'Times New Roman, serif',
              textAlign: 'center',
              fontSize: '1.4rem'
            }}
          >
            ✓ All Questions Completed
          </Typography>
          <Typography 
            variant="h6" 
            sx={{ 
              mt: 2,
              textAlign: 'center',
              color: theme.palette.text.primary,
              fontFamily: 'Times New Roman, serif',
              fontSize: '1.1rem'
            }}
          >
            Correct answers are now displayed below each question.
          </Typography>
        </Box>
      )}

      <Box>
        {qaData.qa_pairs.map((qa, index) => renderQA(qa, index))}
      </Box>

      {!isSubmitted && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 5, mb: 3 }}>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={answeredCount < totalQuestions}
            sx={{ 
              backgroundColor: theme.palette.primary.main,
              color: theme.palette.primary.contrastText,
              borderRadius: 0,
              px: 5,
              py: 2,
              fontSize: '1.3rem',
              fontWeight: 700,
              fontFamily: 'Times New Roman, serif',
              textTransform: 'none',
              border: `3px solid ${theme.palette.primary.main}`,
              '&:hover': {
                backgroundColor: theme.palette.primary.dark
              },
              '&:disabled': {
                backgroundColor: theme.palette.action.disabled,
                color: theme.palette.text.disabled,
                border: `3px solid ${theme.palette.action.disabled}`
              }
            }}
          >
            SUBMIT ANSWERS
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default QAPairs;