import React from 'react';
import { colors, fonts } from './tokens';
import { useReveal, revealStyle } from './useReveal';

// Reusable full-bleed section with paper background and a consistent
// inner container. Used by every non-hero section so vertical rhythm,
// max width, and reveal behavior stay consistent.
const SectionShell = ({
  id,
  eyebrow,
  title,
  lede,
  children,
  dark = false,
  compact = false,
  align = 'left',
}) => {
  const { ref, visible } = useReveal();
  const fg = dark ? '#f3f5fa' : colors.ink700;
  const fgMute = dark ? 'rgba(243, 245, 250, 0.65)' : colors.ink500;
  const eyebrowColor = dark ? 'rgba(158, 181, 221, 0.78)' : colors.ink500;

  return (
    <section
      id={id}
      style={{
        position: 'relative',
        width: '100%',
        background: dark ? colors.ink950 : colors.paper,
        color: fg,
        padding: compact ? '64px 24px' : '96px 24px',
        fontFamily: fonts.sans,
      }}
    >
      <div
        ref={ref}
        style={{
          maxWidth: 1160,
          margin: '0 auto',
          textAlign: align,
        }}
      >
        {(eyebrow || title || lede) && (
          <div
            style={{
              maxWidth: align === 'center' ? 760 : 720,
              margin: align === 'center' ? '0 auto' : 0,
              marginBottom: compact ? 32 : 56,
              ...revealStyle(visible),
            }}
          >
            {eyebrow && (
              <div
                style={{
                  fontSize: 12,
                  letterSpacing: '0.22em',
                  textTransform: 'uppercase',
                  color: eyebrowColor,
                  fontWeight: 600,
                  marginBottom: 16,
                }}
              >
                {eyebrow}
              </div>
            )}
            {title && (
              <h2
                style={{
                  margin: 0,
                  fontFamily: fonts.display,
                  fontWeight: 320,
                  fontSize: 'clamp(34px, 5vw, 60px)',
                  lineHeight: 1.05,
                  letterSpacing: '-0.015em',
                  color: dark ? '#ffffff' : '#0a1024',
                  textWrap: 'balance',
                }}
              >
                {title}
              </h2>
            )}
            {lede && (
              <p
                style={{
                  marginTop: 18,
                  marginBottom: 0,
                  fontSize: 'clamp(15px, 1.25vw, 17px)',
                  lineHeight: 1.55,
                  letterSpacing: '-0.003em',
                  color: fgMute,
                  textWrap: 'pretty',
                  maxWidth: 620,
                }}
              >
                {lede}
              </p>
            )}
          </div>
        )}
        {children}
      </div>
    </section>
  );
};

export default SectionShell;
