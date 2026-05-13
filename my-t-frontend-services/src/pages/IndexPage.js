import React, { useEffect, useState } from 'react';
import { Box } from '@mui/material';
import ProfilePage from './ProfilePage';
import { Header, Footer } from '../components/Layout';
import {
  Hero,
  SectionShell,
  FeatureSpotlight,
  FeatureGridLite,
  ClosingCTA,
  MiniChat,
  MiniDocQA,
  MiniFlashcard,
  MiniStudyPlan,
  MiniMCQ,
  MiniFlowchart,
} from '../components/Landing';
import { colors } from '../components/Landing/tokens';

const IndexPage = () => {
  const [headerVisible, setHeaderVisible] = useState(true);
  const [pastHero, setPastHero] = useState(false);
  const [lastScrollY, setLastScrollY] = useState(0);
  const [profileModalOpen, setProfileModalOpen] = useState(false);

  useEffect(() => {
    const heroSwitch = () => Math.max(360, window.innerHeight * 0.85);
    const onScroll = () => {
      const y = window.scrollY;
      if (y > lastScrollY && y > 200) setHeaderVisible(false);
      else if (y < lastScrollY) setHeaderVisible(true);
      setPastHero(y > heroSwitch());
      setLastScrollY(y);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, [lastScrollY]);

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: colors.paper }}>
      <Header
        isVisible={headerVisible}
        onProfileClick={() => setProfileModalOpen(true)}
        overHero={!pastHero}
      />

      <Hero />

      <SectionShell
        id="features"
        eyebrow="What it does"
        title="More than a chat box."
        lede="Flashcards, quizzes, plans, and visual breakdowns, all in one place."
      >
        <FeatureSpotlight
          eyebrow="Conversation"
          title="Ask anything. Get an answer that makes sense."
          body="Explanations match where you are. Analogies when the idea is new, technical detail once you’re closer. It remembers what you’ve asked, so each answer builds on the last."
          preview={<MiniChat />}
        />
        <FeatureSpotlight
          eyebrow="Document Q&A"
          title="Talk to your readings."
          body="Upload a PDF, a paper, or your own notes. Ask questions and get answers that point to the right page, so you stop scrolling through thirty of them."
          reverse
          preview={<MiniDocQA />}
        />
        <FeatureSpotlight
          eyebrow="Flashcards"
          title="Remember what you learn."
          body="Turn any topic or document into a flashcard deck. Cards come back for review right before you forget them."
          preview={<MiniFlashcard />}
        />
        <FeatureSpotlight
          eyebrow="Study plans"
          title="Know what to do today."
          body="Tell us your goal and your deadline. You get a day by day plan you can adjust when the week gets messy."
          reverse
          preview={<MiniStudyPlan />}
        />
        <FeatureSpotlight
          eyebrow="Practice quizzes"
          title="Test what you learned."
          body="Generate quizzes from any topic or document. Every answer comes with an explanation, so the wrong ones teach you too."
          preview={<MiniMCQ />}
        />
        <FeatureSpotlight
          eyebrow="Visual explanations"
          title="See how it fits together."
          body="Turn heavy text into clean diagrams. Flowcharts and process maps. The shape of a topic shows up before you read every word."
          reverse
          preview={<MiniFlowchart />}
        />

        <FeatureGridLite />
      </SectionShell>

      <ClosingCTA />

      <Footer />

      {profileModalOpen && <ProfilePage onClose={() => setProfileModalOpen(false)} />}
    </Box>
  );
};

export default IndexPage;
