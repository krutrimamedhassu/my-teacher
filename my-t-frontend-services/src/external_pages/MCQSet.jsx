import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  Button,
  Alert,
  Divider
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';

const MCQSet = ({ mcqData }) => {
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [score, setScore] = useState(null);

  // Reset state when new MCQ data is loaded
  useEffect(() => {
    setSelectedAnswers({});
    setIsSubmitted(false);
    setScore(null);
  }, [mcqData]);

  const handleAnswerSelect = (questionIndex, option) => {
    if (!isSubmitted) {
      setSelectedAnswers(prev => ({
        ...prev,
        [questionIndex]: option
      }));
    }
  };

  const isCorrect = (questionIndex, selectedOption) => {
    const question = mcqData.mcqs[questionIndex];
    return selectedOption === question.correct_option;
  };

  const handleSubmit = () => {
    const answeredCount = Object.keys(selectedAnswers).length;
    const totalQuestions = mcqData.mcqs.length;
    
    if (answeredCount < totalQuestions) {
      alert(`Please answer all ${totalQuestions} questions before submitting.`);
      return;
    }

    let correctCount = 0;
    mcqData.mcqs.forEach((mcq, index) => {
      if (selectedAnswers[index] === mcq.correct_option) {
        correctCount++;
      }
    });

    const percentage = Math.round((correctCount / totalQuestions) * 100);
    setScore({ correct: correctCount, total: totalQuestions, percentage });
    setIsSubmitted(true);
  };

  const getGrade = (percentage) => {
    if (percentage >= 90) return 'A';
    if (percentage >= 80) return 'B';
    if (percentage >= 70) return 'C';
    if (percentage >= 60) return 'D';
    return 'F';
  };

  const renderMCQ = (mcq, index) => {
    const isSelected = selectedAnswers[index];
    const isCorrectAnswer = isSelected && isCorrect(index, isSelected);

    return (
      <Box
        key={index}
        sx={{
          mb: 4,
          p: 0,
          pb: 3
        }}
      >
        {/* Question Header */}
        <Box sx={{ mb: 2 }}>
          <Typography 
            variant="h6" 
            sx={{ 
              fontWeight: 600, 
              color: '#2c3e50',
              mb: 1,
              fontSize: '1.1rem',
              lineHeight: 1.4
            }}
          >
            {index + 1}. {mcq.question}
          </Typography>
          
          {/* Progress indicator */}
          {isSubmitted && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              {isCorrectAnswer ? (
                <CheckCircleIcon sx={{ color: '#000000', fontSize: 16 }} />
              ) : (
                <CancelIcon sx={{ color: '#000000', fontSize: 16 }} />
              )}
              <Typography variant="caption" sx={{ color: '#000000', fontWeight: 500 }}>
                {isCorrectAnswer ? 'Correct!' : 'Incorrect'}
              </Typography>
            </Box>
          )}
        </Box>

        {/* Options */}
        <FormControl component="fieldset" sx={{ width: '100%' }}>
          <RadioGroup
            value={selectedAnswers[index] || ''}
            onChange={(e) => handleAnswerSelect(index, e.target.value)}
          >
            {Object.entries(mcq.choices).map(([option, choice]) => {
              const isSelectedOption = selectedAnswers[index] === option;
              const isCorrectOption = option === mcq.correct_option;
              const showCorrect = isSubmitted && isCorrectOption;
              const showIncorrect = isSubmitted && isSelectedOption && !isCorrectOption;

              return (
                <FormControlLabel
                  key={option}
                  value={option}
                  control={
                    <Radio 
                      disabled={isSubmitted}
                      size="small"
                      sx={{
                        color: '#9e9e9e',
                        '&.Mui-checked': {
                          color: '#000000'
                        }
                      }}
                    />
                  }
                  label={
                    <Box sx={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: 1,
                      width: '100%'
                    }}>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          fontWeight: 400,
                          color: '#34495e',
                          flex: 1,
                          fontSize: '0.9rem',
                          lineHeight: 1.5
                        }}
                      >
                        {option}. {choice}
                      </Typography>
                      {showCorrect && (
                        <CheckCircleIcon sx={{ color: '#000000', fontSize: 16 }} />
                      )}
                      {showIncorrect && (
                        <CancelIcon sx={{ color: '#000000', fontSize: 16 }} />
                      )}
                    </Box>
                  }
                  sx={{
                    mb: 1,
                    p: 1.5,
                    border: '1px solid #ecf0f1',
                    borderRadius: 1,
                    backgroundColor: showCorrect ? '#f5f5f5' : 
                                   showIncorrect ? '#f5f5f5' : 
                                   isSelectedOption ? '#f5f5f5' : '#ffffff',
                    '&:hover': {
                      backgroundColor: isSubmitted ? 'inherit' : '#f8f8f8',
                      borderColor: '#9e9e9e'
                    },
                    '&.Mui-checked': {
                      backgroundColor: '#f5f5f5',
                      borderColor: '#000000'
                    },
                    transition: 'all 0.2s ease-in-out'
                  }}
                />
              );
            })}
          </RadioGroup>
        </FormControl>

        {/* Solution */}
        {isSubmitted && (
          <Box sx={{ 
            mt: 2, 
            p: 2, 
            backgroundColor: '#f8f9fa', 
            borderRadius: 1,
            border: '1px solid #e9ecef'
          }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: '#2c3e50', fontSize: '0.85rem' }}>
              Correct Answer: {mcq.correct_option}. {mcq.answer}
            </Typography>
            <Divider sx={{ my: 1, borderColor: '#ecf0f1' }} />
            <Typography variant="body2" sx={{ color: '#7f8c8d', lineHeight: 1.5, fontSize: '0.85rem' }}>
              <strong>Solution:</strong> {mcq.solution}
            </Typography>
          </Box>
        )}
      </Box>
    );
  };

  const answeredCount = Object.keys(selectedAnswers).length;
  const totalQuestions = mcqData.mcqs.length;

  return (
    <Box sx={{ p: 3, maxWidth: '800px', margin: '0 auto' }}>
      {/* Header */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography 
          variant="h5" 
          sx={{ 
            fontWeight: 700, 
            color: '#2c3e50',
            mb: 2,
            fontSize: '1.5rem'
          }}
        >
          Multiple Choice Questions
        </Typography>
        
        {!isSubmitted && (
          <Alert 
            severity="info" 
            sx={{ 
              mb: 2,
              backgroundColor: '#f5f5f5',
              color: '#000000',
              border: '1px solid #e0e0e0',
              fontSize: '0.85rem'
            }}
          >
            Answer all questions and click Submit to see your results.
          </Alert>
        )}
        
        {!isSubmitted && (
          <Typography 
            variant="body2" 
            sx={{ 
              mb: 2,
              color: '#7f8c8d',
              fontWeight: 500,
              fontSize: '0.9rem'
            }}
          >
            Progress: {answeredCount}/{totalQuestions} questions answered
          </Typography>
        )}
      </Box>

      {/* Score Display */}
      {isSubmitted && score && (
        <Box
          sx={{ 
            mb: 4, 
            p: 3, 
            backgroundColor: '#ffffff',
            border: '2px solid #000000',
            borderRadius: 2,
            textAlign: 'center',
            boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)'
          }}
        >
          <Typography 
            variant="h6" 
            sx={{ 
              fontWeight: 700, 
              color: '#2c3e50',
              mb: 1,
              fontSize: '1.2rem'
            }}
          >
            Your Score: {score.correct}/{score.total} ({score.percentage}%)
          </Typography>
          <Typography 
            variant="h5" 
            sx={{ 
              fontWeight: 800, 
              color: '#000000',
              mb: 2,
              fontSize: '1.8rem'
            }}
          >
            Grade: {getGrade(score.percentage)}
          </Typography>
          <Typography 
            variant="body2" 
            sx={{ 
              color: '#7f8c8d',
              fontStyle: 'italic',
              fontSize: '0.85rem'
            }}
          >
            Review your answers and solutions below
          </Typography>
        </Box>
      )}

      {/* Questions */}
      <Box>
        {mcqData.mcqs.map((mcq, index) => renderMCQ(mcq, index))}
      </Box>

      {/* Submit Button */}
      {!isSubmitted && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 5, mb: 2 }}>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={answeredCount < totalQuestions}
            sx={{ 
              backgroundColor: '#000000',
              color: '#ffffff',
              px: 4,
              py: 1.5,
              fontSize: '1rem',
              fontWeight: 600,
              borderRadius: 2,
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
              '&:hover': {
                backgroundColor: '#333333',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
              },
              '&:disabled': {
                backgroundColor: '#cccccc',
                color: '#999999',
                boxShadow: 'none'
              }
            }}
          >
            Submit Answers
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default MCQSet;