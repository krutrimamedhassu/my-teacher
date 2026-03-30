import React from 'react';
import { Box, Typography } from '@mui/material';
import DocumentsList from './DocumentsList';
import Flashcard from '../../external_pages/Flashcard';
import TopicBreakdown from '../../external_pages/TopicBreakdown';
import KeyConcepts from '../../external_pages/KeyConcepts';
import MCQSet from '../../external_pages/MCQSet';
import QAPairs from '../../external_pages/QAPairs';
import StudyPlan from '../../external_pages/StudyPlan';
import VisualFlowchart from '../../external_pages/VisualFlowchart';

const RightSidebar = ({
  theme,
  open = false,
  currentTool = 'Learning Tools',
  qaPairs = null,
  uploadedDocuments = [],
  flashcards = null,
  topicBreakdown = null,
  keyConcepts = null,
  mcqSet = null,
  studyPlan = null,
  visualData = null,
  rightSidebarWidth = 840,
  isMobile = false,
  isResizing = false,
  onClose,
  onToggleOpen,
  onDeleteDocument,
  onCycleSidebarInfo,
  onCycleSidebarInfoReverse,
  onMouseDown
}) => {
  console.log('📱 RightSidebar: Component rendered with props:', {
    open,
    currentTool,
    qaPairsCount: qaPairs?.qa_pairs?.length || 0,
    documentsCount: uploadedDocuments?.length || 0,
    flashcardsCount: flashcards?.flashcards?.length || 0,
    topicBreakdownCount: topicBreakdown?.topics?.length || 0,
    keyConceptsCount: keyConcepts?.concepts?.length || 0,
    keyConceptsData: keyConcepts,
    mcqSetCount: mcqSet?.mcqs?.length || 0,
    mcqSetData: mcqSet,
    studyPlanCount: studyPlan?.study_sessions?.length || 0,
    studyPlanData: studyPlan,
    visualDataCount: visualData?.elements?.length || 0,
    visualDataData: visualData,
    rightSidebarWidth,
    isMobile,
    isResizing
  });

  return (
    <Box
      sx={{
        position: 'relative',
        height: '100vh',
        width: (() => {
          if (!open) return 48;
          if (isMobile) return '100vw';
          
          // Calculate max width to prevent overflow
          const leftSidebarWidth = 48; // Assuming minimal left sidebar when right is open
          const minChatWidth = 300;
          const maxRightSidebarWidth = window.innerWidth - leftSidebarWidth - minChatWidth;
          
          return Math.min(rightSidebarWidth || 840, Math.max(260, maxRightSidebarWidth));
        })(),
        flexShrink: 0,
        bgcolor: open ? '#f5f5f5' : 'white',
        borderLeft: `1px solid ${theme.palette.divider}`,
        zIndex: theme.zIndex.drawer + 1,
        display: 'flex',
        flexDirection: 'column',
        transition: isResizing ? 'none' : 'width 0.2s cubic-bezier(0.4,0,0.2,1)',
      }}
    >
      {/* Resize handle */}
      {open && !isMobile && (
        <Box
          sx={{
            position: 'absolute',
            left: -4,
            top: 0,
            width: 8,
            height: '100%',
            cursor: 'col-resize',
            zIndex: theme.zIndex.drawer + 2,
            '&:hover': {
              backgroundColor: theme.palette.primary.main,
              opacity: 0.3,
            },
            '&:active': {
              backgroundColor: theme.palette.primary.main,
              opacity: 0.5,
            }
          }}
          onMouseDown={onMouseDown}
        />
      )}
      
      {open ? (
        <Box sx={{
          pt: 2.3,
          px: 2,
          mb: 2,
          height: '100%',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <Box sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 2,
            flexShrink: 0
          }}>
            <Box
              sx={{
                width: 24,
                height: 24,
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                transition: 'all 0.2s ease-in-out',
                '&:hover': {
                  transform: 'scale(1.05)',
                  bgcolor: theme.palette.action.hover,
                },
              }}
              onClick={() => {
                console.log('📱 RightSidebar: Close button clicked');
                onClose();
              }}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 32 32"
                width="20"
                height="20"
                fill="none"
                stroke="#666666"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <rect x="3" y="3" width="26" height="26" rx="4"/>
                <line x1="19" y1="3" x2="19" y2="29"/>
              </svg>
            </Box>
            <Typography variant="h6" sx={{ flex: 1, textAlign: 'center' }}>
              {currentTool === 'Documents' 
                ? `Uploaded Documents (${uploadedDocuments.length} are available in this chat)`
                : currentTool === 'Flashcards'
                ? `Flashcards (${flashcards?.flashcards?.length || 0})`
                : currentTool === 'QA Pairs'
                ? `Q&A Pairs (${qaPairs?.qa_pairs?.length || 0})`
                : currentTool === 'Topic Breakdown'
                ? `Topic Breakdown (${topicBreakdown?.topics?.length || 0})`
                : currentTool === 'Key Concepts'
                ? `Key Concepts (${keyConcepts?.concepts?.length || 0})`
                : currentTool === 'MCQ Set'
                ? `MCQ Set (${mcqSet?.mcqs?.length || 0})`
                : currentTool === 'Tools'
                ? (() => {
                    // Intelligently show what tools are available
                    if (mcqSet && mcqSet.mcqs && mcqSet.mcqs.length > 0) {
                      return `Tools - MCQ Set (${mcqSet.mcqs.length})`;
                    } else if (keyConcepts && keyConcepts.concepts && keyConcepts.concepts.length > 0) {
                      return `Tools - Key Concepts (${keyConcepts.concepts.length})`;
                    } else if (topicBreakdown && topicBreakdown.topics && topicBreakdown.topics.length > 0) {
                      return `Tools - Topic Breakdown (${topicBreakdown.topics.length})`;
                    } else if (flashcards && flashcards.flashcards && flashcards.flashcards.length > 0) {
                      return `Tools - Flashcards (${flashcards.flashcards.length})`;
                    } else if (qaPairs && qaPairs.qa_pairs && qaPairs.qa_pairs.length > 0) {
                      return `Tools - Q&A Pairs (${qaPairs.qa_pairs.length})`;
                    } else if (studyPlan && studyPlan.study_sessions && studyPlan.study_sessions.length > 0) {
                      return `Tools - Study Plan (${studyPlan.study_sessions.length} days)`;
                    } else if (visualData && (visualData.elements || visualData.visual_type)) {
                      return `Tools - ${visualData.visual_type || 'Visual'} (${visualData.elements?.length || 0} elements)`;
                    } else {
                      return `Tools (0)`;
                    }
                  })()
                : currentTool
              }
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'row', gap: 0.5, alignItems: 'center' }}>
              <Box
                sx={{
                  width: 28,
                  height: 28,
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'scale(1.05)',
                    bgcolor: theme.palette.action.hover,
                  },
                }}
                onClick={() => {
                  console.log('📱 RightSidebar: Left arrow clicked');
                  onCycleSidebarInfoReverse && onCycleSidebarInfoReverse();
                }}
              >
                <img src="/left-arrow-icon.svg" alt="Previous" width="24" height="24" />
              </Box>
              <Box
                sx={{
                  width: 28,
                  height: 28,
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'scale(1.05)',
                    bgcolor: theme.palette.action.hover,
                  },
                }}
                onClick={() => {
                  console.log('📱 RightSidebar: Right arrow clicked');
                  onCycleSidebarInfo();
                }}
              >
                <img src="/right-arrow-icon.svg" alt="Next" width="24" height="24" />
              </Box>
            </Box>
          </Box>

          <Box sx={{
            flex: 1,
            overflow: 'auto',
            width: '100%',
            '&::-webkit-scrollbar': {
              display: 'none'
            },
            '-ms-overflow-style': 'none',
            'scrollbarWidth': 'none',
          }}>
            {currentTool === 'Documents' && (
              <DocumentsList
                documents={uploadedDocuments}
                onDeleteDocument={onDeleteDocument}
                theme={theme}
              />
            )}

            {currentTool === 'QA Pairs' && qaPairs && qaPairs.qa_pairs && (
              <Box sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Q&A Pairs ({qaPairs.qa_pairs.length})
                </Typography>
                {qaPairs.qa_pairs.map((pair, index) => (
                  <Box key={pair.question || `qa-${index}`} sx={{ mb: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                      Q: {pair.question}
                    </Typography>
                    <Typography variant="body2">
                      A: {pair.answer || 'No answer provided yet.'}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}

            {(currentTool === 'Flashcards' || (currentTool === 'Tools' && flashcards && flashcards.flashcards)) && flashcards && flashcards.flashcards && (
              <Box className="flashcards-grid-sidebar">
                {flashcards.flashcards.map((flashcard) => (
                  <Flashcard
                    key={`flashcard-${String(flashcard?.question ?? '').slice(0, 20)}-${String(flashcard?.answer ?? '').slice(0, 10)}`}
                    question={flashcard?.question}
                    answer={flashcard?.answer}
                    subject={flashcards.subject_area || 'General'}
                    difficulty={flashcards.difficulty_level || 'Medium'}
                  />
                ))}
              </Box>
            )}

            {(currentTool === 'QAPairs' || (currentTool === 'Tools' && qaPairs && qaPairs.qa_pairs)) && qaPairs && qaPairs.qa_pairs && (
              <QAPairs qaData={qaPairs} theme={theme} />
            )}

            {(currentTool === 'StudyPlan' || (currentTool === 'Tools' && studyPlan && studyPlan.study_sessions)) && studyPlan && studyPlan.study_sessions && (
              <StudyPlan plan={studyPlan} theme={theme} isSidebar={true} />
            )}

            {(currentTool === 'VisualFlowchart' || (currentTool === 'Tools' && visualData && (visualData.elements || visualData.visual_type))) && visualData && (
              <VisualFlowchart data={visualData} theme={theme} />
            )}

            {(currentTool === 'Topic Breakdown' || (currentTool === 'Tools' && topicBreakdown && topicBreakdown.topics)) && topicBreakdown && topicBreakdown.topics && (
              <TopicBreakdown breakdownData={topicBreakdown} theme={theme} />
            )}

            {(currentTool === 'Key Concepts' || (currentTool === 'Tools' && keyConcepts && keyConcepts.concepts)) && keyConcepts && keyConcepts.concepts && (
              <KeyConcepts conceptsData={keyConcepts} theme={theme} />
            )}

            {(currentTool === 'MCQ Set' || (currentTool === 'Tools' && mcqSet && mcqSet.mcqs)) && mcqSet && mcqSet.mcqs && (
              <MCQSet mcqData={mcqSet} />
            )}
            

            {currentTool === 'Tools' && (!flashcards || !flashcards.flashcards) && (!topicBreakdown || !topicBreakdown.topics) && (!keyConcepts || !keyConcepts.concepts) && (!mcqSet || !mcqSet.mcqs) && (!qaPairs || !qaPairs.qa_pairs) && (!studyPlan || !studyPlan.study_sessions) && (!visualData || (!visualData.elements && !visualData.visual_type)) && (
              <Box sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  No tools available yet. Try asking me to generate flashcards, topic breakdowns, key concepts, or MCQ sets!
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      ) : (
        <Box
          sx={{
            width: '100%',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            pt: 3,
            gap: 1,
            justifyContent: 'flex-start',
          }}
        >
          <Box
            sx={{
              width: 24,
              height: 24,
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                transform: 'scale(1.05)',
                bgcolor: theme.palette.action.hover,
              },
            }}
            onClick={() => {
              console.log('📱 RightSidebar: Toggle button clicked, restoring last tool');
              onToggleOpen();
            }}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 32 32"
              width="20"
              height="20"
              fill="none"
              stroke="#666666"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="3" y="3" width="26" height="26" rx="4"/>
              <line x1="19" y1="3" x2="19" y2="29"/>
            </svg>
          </Box>
          {/* 16px gap between sidebar toggle and stacked books icon to match left sidebar */}
          <Box sx={{ height: '16px' }} />
          <Box
            sx={{
              width: 24,
              height: 24,
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                transform: 'scale(1.05)',
                bgcolor: theme.palette.action.hover,
              },
            }}
            onClick={() => {
              console.log('📱 RightSidebar: Documents button clicked, opening Documents sidebar');
              onToggleOpen('Documents');
            }}
          >
            <img src="/stacked-books.svg" alt="Documents" width="16" height="16" />
          </Box>

        </Box>
      )}
    </Box>
  );
};

export default RightSidebar;