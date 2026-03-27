import React, { useState } from 'react';
import {
  Box,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  List,
  ListItem,
  ListItemText
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

const KeyConcepts = ({ conceptsData, theme }) => {
  const [expanded, setExpanded] = useState(new Set(['concepts', 'definitions']));

  const handleAccordionChange = (section) => (event, isExpanded) => {
    const newExpanded = new Set(expanded);
    if (isExpanded) {
      newExpanded.add(section);
    } else {
      newExpanded.delete(section);
    }
    setExpanded(newExpanded);
  };

  const getTypeLabel = (type) => {
    switch (type) {
      case 'concept':
        return 'Concept';
      case 'definition':
        return 'Definition';
      case 'formula':
        return 'Formula';
      case 'takeaway':
        return 'Takeaway';
      case 'relationship':
        return 'Relationship';
      default:
        return type;
    }
  };

  const groupByType = () => {
    const grouped = {};
    conceptsData.concepts.forEach(concept => {
      if (!grouped[concept.type]) {
        grouped[concept.type] = [];
      }
      grouped[concept.type].push(concept);
    });
    return grouped;
  };

  const groupedConcepts = groupByType();

  const renderConceptItem = (concept, index) => (
    <ListItem
      key={index}
      sx={{
        py: 1.5,
        px: 2,
        mb: 1,
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: 1,
        backgroundColor: theme.palette.background.paper,
        '&:hover': {
          backgroundColor: theme.palette.action.hover,
        }
      }}
    >
      <ListItemText
        primary={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
            <Chip
              label={getTypeLabel(concept.type)}
              size="small"
              variant="outlined"
              sx={{
                fontWeight: 600,
                fontSize: '0.7rem'
              }}
            />
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              {concept.content}
            </Typography>
          </Box>
        }
        secondary={
          concept.description && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {concept.description}
            </Typography>
          )
        }
      />
    </ListItem>
  );

  const renderSection = (type, concepts) => (
    <Accordion
      key={type}
      expanded={expanded.has(type)}
      onChange={handleAccordionChange(type)}
      sx={{
        mb: 1,
        '&:before': { display: 'none' },
        boxShadow: 'none',
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: 1
      }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{
          backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.01)',
          borderRadius: 1,
          '&:hover': {
            backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.03)'
          }
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Chip
            label={getTypeLabel(type)}
            size="small"
            variant="outlined"
            sx={{
              fontWeight: 600
            }}
          />
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            {getTypeLabel(type)}s ({concepts.length})
          </Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ pt: 1, pb: 2 }}>
        <List sx={{ p: 0 }}>
          {concepts.map((concept, index) => renderConceptItem(concept, index))}
        </List>
      </AccordionDetails>
    </Accordion>
  );

  return (
    <Box sx={{ p: 1 }}>
      <Box>
        {Object.entries(groupedConcepts).map(([type, concepts]) => 
          renderSection(type, concepts)
        )}
      </Box>
    </Box>
  );
};

export default KeyConcepts;