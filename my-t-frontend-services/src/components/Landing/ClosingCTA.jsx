import React from 'react';
import { Link } from 'react-router-dom';
import { colors, fonts, ease } from './tokens';
import { useReveal, revealStyle } from './useReveal';

const ClosingCTA = () => {
  const { ref, visible } = useReveal();
  return (
    <section
      style={{
        background: colors.ink950,
        color: '#f3f5fa',
        padding: '96px 24px',
        textAlign: 'center',
        fontFamily: fonts.sans,
      }}
    >
      <div
        ref={ref}
        style={{
          maxWidth: 720,
          margin: '0 auto',
          ...revealStyle(visible),
        }}
      >
        <h2
          style={{
            margin: 0,
            fontFamily: fonts.display,
            fontWeight: 320,
            fontSize: 'clamp(36px, 5.8vw, 64px)',
            lineHeight: 1.05,
            letterSpacing: '-0.015em',
            color: '#ffffff',
          }}
        >
          Start with one question.
        </h2>
        <p
          style={{
            marginTop: 18,
            marginBottom: 32,
            fontSize: 17,
            lineHeight: 1.55,
            color: 'rgba(243, 245, 250, 0.62)',
            fontWeight: 400,
          }}
        >
          Bring something you don’t fully get. Leave with a version that makes sense.
        </p>
        <Link
          to="/chat"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            padding: '13px 24px',
            borderRadius: 999,
            background: '#000000',
            color: '#ffffff',
            fontWeight: 500,
            fontSize: 15,
            textDecoration: 'none',
            border: '1px solid rgba(255, 255, 255, 0.18)',
            transition: `transform 220ms ${ease.outQuint}, background 220ms ${ease.outQuint}`,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-1px)';
            e.currentTarget.style.background = '#1a1a1a';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.background = '#000000';
          }}
        >
          Start learning
          <span aria-hidden style={{ fontSize: 18, lineHeight: 1 }}>→</span>
        </Link>
      </div>
    </section>
  );
};

export default ClosingCTA;
