import React, { useState } from 'react';
import {
  Box,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Paper,
  Chip
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

const TopicBreakdown = ({ breakdownData, theme }) => {
  const [expanded, setExpanded] = useState(new Set());

  const handleAccordionChange = (topicId) => (event, isExpanded) => {
    const newExpanded = new Set(expanded);
    if (isExpanded) {
      newExpanded.add(topicId);
    } else {
      newExpanded.delete(topicId);
    }
    setExpanded(newExpanded);
  };

  const renderTopic = (topic, level = 0) => {
    const hasChildren = breakdownData.topics.some(t => 
      t.id.startsWith(topic.id + '.') && t.id.split('.').length === level + 2
    );
    
    const childTopics = breakdownData.topics.filter(t => 
      t.id.startsWith(topic.id + '.') && t.id.split('.').length === level + 2
    );

    if (hasChildren) {
      return (
        <Accordion
          key={topic.id}
          expanded={expanded.has(topic.id)}
          onChange={handleAccordionChange(topic.id)}
          sx={{
            mb: 1.5,
            '&:before': { display: 'none' },
            boxShadow: 'none',
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: 2,
            backgroundColor: theme.palette.background.paper
          }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{
              backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.01)',
              borderRadius: 2,
              '&:hover': {
                backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.03)'
              },
              '& .MuiAccordionSummary-content': {
                margin: '12px 0'
              }
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
              <Chip 
                label={topic.id} 
                size="small" 
                variant="outlined"
                sx={{ 
                  minWidth: '45px',
                  fontWeight: 600,
                  fontSize: '0.75rem'
                }}
              />
              <Typography variant="subtitle1" sx={{ fontWeight: 600, color: theme.palette.text.primary }}>
                {topic.title}
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ pt: 2, pb: 2, px: 3 }}>
            <Typography 
              variant="body2" 
              color="text.secondary" 
              sx={{ 
                mb: 3,
                lineHeight: 1.6,
                fontSize: '0.875rem'
              }}
            >
              {topic.summary}
            </Typography>
            <Box sx={{ pl: 1 }}>
              {childTopics.map(childTopic => renderTopic(childTopic, level + 1))}
            </Box>
          </AccordionDetails>
        </Accordion>
      );
    } else {
      return (
        <Paper
          key={topic.id}
          elevation={0}
          sx={{
            p: 2.5,
            mb: 1.5,
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: 2,
            backgroundColor: theme.palette.background.paper
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 1.5 }}>
            <Chip 
              label={topic.id} 
              size="small" 
              variant="outlined"
              sx={{ 
                minWidth: '45px',
                fontWeight: 600,
                fontSize: '0.75rem',
                flexShrink: 0
              }}
            />
            <Typography variant="subtitle1" sx={{ fontWeight: 600, color: theme.palette.text.primary }}>
              {topic.title}
            </Typography>
          </Box>
          <Typography 
            variant="body2" 
            color="text.secondary"
            sx={{ 
              lineHeight: 1.6,
              fontSize: '0.875rem',
              pl: 6.5
            }}
          >
            {topic.summary}
          </Typography>
        </Paper>
      );
    }
  };

  const mainTopics = breakdownData.topics.filter(topic => 
    topic.id.split('.').length === 1
  );

  return (
    <Box sx={{ p: 1 }}>
      <Box>
        {mainTopics.map(topic => renderTopic(topic))}
      </Box>
    </Box>
  );
};

export default TopicBreakdown;