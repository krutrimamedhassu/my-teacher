import React from 'react';
import { Link } from 'react-router-dom';
import { colors, fonts, ease } from './tokens';
import { useReveal, revealStyle } from './useReveal';
import './Landing.css';

// Alternating two-column row inside a Section: copy on one side, miniature
// on the other. The miniature is the actual product surface in miniature.
// This is the "show the product" pattern.
const FeatureSpotlight = ({
  eyebrow,
  title,
  body,
  ctaText = 'Try it →',
  ctaTo = '/chat',
  reverse = false,
  preview,
}) => {
  const { ref, visible } = useReveal();

  const copy = (
    <div style={{ ...revealStyle(visible) }}>
      <div
        style={{
          fontSize: 11,
          letterSpacing: '0.22em',
          textTransform: 'uppercase',
          color: colors.ink500,
          fontWeight: 600,
          marginBottom: 16,
        }}
      >
        {eyebrow}
      </div>
      <h3
        style={{
          margin: 0,
          fontFamily: fonts.display,
          fontWeight: 320,
          fontSize: 'clamp(28px, 3.6vw, 44px)',
          lineHeight: 1.08,
          letterSpacing: '-0.012em',
          color: '#0a1024',
          textWrap: 'balance',
        }}
      >
        {title}
      </h3>
      <p
        style={{
          marginTop: 16,
          marginBottom: 24,
          fontSize: 'clamp(15px, 1.2vw, 17px)',
          lineHeight: 1.6,
          color: colors.ink500,
          letterSpacing: '-0.003em',
          maxWidth: 460,
          fontWeight: 400,
        }}
      >
        {body}
      </p>
      <Link
        to={ctaTo}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          fontSize: 14,
          fontWeight: 500,
          color: colors.ink700,
          textDecoration: 'none',
          borderBottom: `1px solid ${colors.ink700}`,
          paddingBottom: 2,
          transition: `color 200ms ${ease.outQuint}, border-color 200ms ${ease.outQuint}`,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.color = colors.ink500;
          e.currentTarget.style.borderColor = colors.ink500;
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.color = colors.ink700;
          e.currentTarget.style.borderColor = colors.ink700;
        }}
      >
        {ctaText}
      </Link>
    </div>
  );

  const previewBlock = (
    <div
      style={{
        ...revealStyle(visible, { delay: 120 }),
        display: 'flex',
        justifyContent: reverse ? 'flex-start' : 'flex-end',
      }}
    >
      <div style={{ width: '100%', maxWidth: 460 }}>{preview}</div>
    </div>
  );

  return (
    <div ref={ref} className={`spotlight-grid${reverse ? ' reverse' : ''}`}>
      {reverse ? (
        <>
          {previewBlock}
          {copy}
        </>
      ) : (
        <>
          {copy}
          {previewBlock}
        </>
      )}
    </div>
  );
};

export default FeatureSpotlight;
