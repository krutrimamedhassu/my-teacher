import React from 'react';
import { Box, Typography, Paper, Chip } from '@mui/material';

export default function StudyPlan({ plan, theme, isSidebar = false }) {
  if (!plan) return null;

  const {
    study_sessions = [],
    subject_area,
    knowledge_level,
    total_days,
    total_hours,
    learning_goals = [],
  } = plan;

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return theme.palette.error.main;
      case 'medium': return theme.palette.warning.main;
      case 'low': return theme.palette.success.main;
      default: return theme.palette.text.secondary;
    }
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'challenging': return theme.palette.error.main;
      case 'moderate': return theme.palette.warning.main;
      case 'easy': return theme.palette.success.main;
      default: return theme.palette.text.secondary;
    }
  };

  return (
    <Box sx={{ width: '100%', maxWidth: isSidebar ? '100%' : 900, margin: '0 auto', p: 3 }}>
      {/* Plan Summary */}
      <Paper 
        elevation={0}
        sx={{
          border: `2px solid ${theme.palette.divider}`,
          background: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.05)' : '#f8f8f8',
          borderRadius: 0,
          p: 3,
          mb: 4,
          textAlign: 'center',
        }}
      >
        <Typography 
          variant="h3" 
          sx={{ 
            margin: 0, 
            fontWeight: 700, 
            fontSize: '2rem', 
            color: theme.palette.text.primary,
            fontFamily: 'Times New Roman, serif',
            mb: 2
          }}
        >
          📚 STUDY PLAN
        </Typography>
        <Typography 
          variant="h6" 
          sx={{ 
            fontSize: '1.1rem', 
            color: theme.palette.text.primary, 
            mb: 1,
            fontFamily: 'Times New Roman, serif'
          }}
        >
          <strong>Subject:</strong> {subject_area} • <strong>Level:</strong> {knowledge_level}
        </Typography>
        <Typography 
          variant="h6" 
          sx={{ 
            fontSize: '1.1rem', 
            color: theme.palette.text.primary, 
            mb: 1,
            fontFamily: 'Times New Roman, serif'
          }}
        >
          <strong>Total Days:</strong> {total_days} • <strong>Total Hours:</strong> {total_hours}
        </Typography>
        <Typography 
          variant="h6" 
          sx={{ 
            fontSize: '1.1rem', 
            color: theme.palette.text.primary,
            fontFamily: 'Times New Roman, serif'
          }}
        >
          <strong>Goals:</strong> {learning_goals.join(', ')}
        </Typography>
      </Paper>

      {/* Study Sessions */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {study_sessions.map((session) => (
          <Paper
            key={`session-${session.day}-${session.date}`}
            elevation={0}
            sx={{
              border: `2px solid ${theme.palette.divider}`,
              background: theme.palette.background.paper,
              borderRadius: 0,
              p: 2.5,
              width: '100%',
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography 
                variant="h6" 
                sx={{ 
                  fontWeight: 700, 
                  fontSize: '1.1rem', 
                  color: theme.palette.text.primary,
                  fontFamily: 'Times New Roman, serif'
                }}
              >
                Day {session.day} — {session.date}
              </Typography>
              <Chip 
                label={`${session.duration_hours} hrs`}
                sx={{ 
                  fontWeight: 600, 
                  color: '#fff', 
                  bgcolor: theme.palette.text.primary,
                  fontSize: '0.95rem',
                  fontFamily: 'Times New Roman, serif'
                }}
              />
            </Box>
            
            <Typography 
              variant="body1" 
              sx={{ 
                mb: 1, 
                fontFamily: 'Times New Roman, serif',
                color: theme.palette.text.primary
              }}
            >
              <strong>Topics:</strong> {session.topics.join(', ')}
            </Typography>
            
            <Typography 
              variant="body1" 
              sx={{ 
                mb: 1, 
                fontFamily: 'Times New Roman, serif',
                color: theme.palette.text.primary
              }}
            >
              <strong>Activities:</strong> {session.activities.join(', ')}
            </Typography>
            
            <Typography 
              variant="body1" 
              sx={{ 
                mb: 1, 
                fontFamily: 'Times New Roman, serif',
                color: theme.palette.text.primary
              }}
            >
              <strong>Resources:</strong> {session.resources.join(', ')}
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
              <Typography 
                variant="body1" 
                sx={{ 
                  fontFamily: 'Times New Roman, serif',
                  color: theme.palette.text.primary
                }}
              >
                <strong>Priority:</strong>
              </Typography>
              <Chip 
                label={session.priority}
                size="small"
                sx={{ 
                  color: '#fff',
                  bgcolor: getPriorityColor(session.priority),
                  fontWeight: 600,
                  fontFamily: 'Times New Roman, serif'
                }}
              />
              <Typography 
                variant="body1" 
                sx={{ 
                  fontFamily: 'Times New Roman, serif',
                  color: theme.palette.text.primary
                }}
              >
                <strong>Difficulty:</strong>
              </Typography>
              <Chip 
                label={session.estimated_difficulty}
                size="small"
                sx={{ 
                  color: '#fff',
                  bgcolor: getDifficultyColor(session.estimated_difficulty),
                  fontWeight: 600,
                  fontFamily: 'Times New Roman, serif'
                }}
              />
            </Box>
            
            <Typography 
              variant="body1" 
              sx={{ 
                mb: 1, 
                fontFamily: 'Times New Roman, serif',
                color: theme.palette.text.primary
              }}
            >
              <strong>Learning Objectives:</strong>
            </Typography>
            <Box component="ul" sx={{ m: '4px 0 0 18px', p: 0 }}>
              {session.learning_objectives.map((obj) => (
                <Typography 
                  component="li" 
                  key={`objective-${session.day}-${obj}`} 
                  variant="body1"
                  sx={{ 
                    fontSize: '1rem', 
                    color: theme.palette.text.primary,
                    fontFamily: 'Times New Roman, serif',
                    mb: 0.5
                  }}
                >
                  {obj}
                </Typography>
              ))}
            </Box>
          </Paper>
        ))}
      </Box>
    </Box>
  );
}