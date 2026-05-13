import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import AuroraField from './AuroraField';
import { colors, fonts, ease } from './tokens';

// Inline SVG noise as a data URI for the grain layer. Fixes the "plastic"
// look that flat dark UIs have on non-OLED screens.
const grainBg =
  "url(\"data:image/svg+xml;utf8,<svg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix type='matrix' values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.5 0'/></filter><rect width='100%' height='100%' filter='url(%23n)' opacity='0.55'/></svg>\")";

const TRUST = [
  'Free to start',
  'No card needed',
  'Your work stays private',
];

const Hero = () => {
  const heroRef = useRef(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const id = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const stagger = (i) => ({
    opacity: mounted ? 1 : 0,
    transform: mounted ? 'translateY(0)' : 'translateY(18px)',
    transition: `opacity 700ms ${ease.outQuint} ${i * 90}ms, transform 700ms ${ease.outQuint} ${i * 90}ms`,
  });

  const scrollToFeatures = (e) => {
    e.preventDefault();
    const el = document.getElementById('features');
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <section
      ref={heroRef}
      style={{
        position: 'relative',
        width: '100%',
        minHeight: '100vh',
        maxHeight: 980,
        background: colors.ink950,
        overflow: 'hidden',
        isolation: 'isolate',
        fontFamily: fonts.sans,
        color: '#f3f5fa',
      }}
    >
      {/* layer 0: shader */}
      <AuroraField containerRef={heroRef} />

      {/* layer 1: soft floor-light bottom blend */}
      <div
        aria-hidden
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 1,
          pointerEvents: 'none',
          background: `radial-gradient(150% 30% at 50% 122%, ${colors.paper} 0%, transparent 65%)`,
          opacity: 0.6,
        }}
      />

      {/* layer 2: film grain */}
      <div
        aria-hidden
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 2,
          pointerEvents: 'none',
          backgroundImage: grainBg,
          backgroundSize: '200px 200px',
          opacity: 0.06,
          mixBlendMode: 'overlay',
        }}
      />

      {/* layer 3: content */}
      <div
        style={{
          position: 'relative',
          zIndex: 3,
          height: '100%',
          minHeight: '100vh',
          maxHeight: 980,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          padding: '96px 24px',
          textAlign: 'center',
        }}
      >
        <div style={{ maxWidth: 920 }}>
          <h1
            style={{
              ...stagger(0),
              fontFamily: fonts.display,
              fontWeight: 800,
              fontSize: 'clamp(48px, 9vw, 120px)',
              letterSpacing: '-0.02em',
              lineHeight: 1.0,
              margin: 0,
              marginBottom: 14,
              color: '#c8d0de',
              textTransform: 'uppercase',
              textWrap: 'balance',
            }}
          >
            My Teacher
          </h1>

          <div
            style={{
              ...stagger(1),
              fontSize: 12,
              letterSpacing: '0.22em',
              textTransform: 'uppercase',
              color: 'rgba(158, 181, 221, 0.6)',
              fontWeight: 600,
              marginBottom: 28,
              fontFamily: fonts.sans,
            }}
          >
            AI Learning Platform
          </div>

          <p
            style={{
              ...stagger(2),
              fontFamily: fonts.sans,
              fontWeight: 400,
              fontSize: 'clamp(17px, 1.5vw, 20px)',
              lineHeight: 1.55,
              letterSpacing: '-0.005em',
              color: 'rgba(243, 245, 250, 0.72)',
              margin: '0 auto 36px',
              maxWidth: 620,
              textWrap: 'balance',
            }}
          >
            Your AI tutor for anything you want to learn. Ask a question, get a clear answer,
            and practice with cards and quizzes built around what you’re studying.
          </p>

          <div
            style={{
              ...stagger(3),
              display: 'flex',
              gap: 14,
              justifyContent: 'center',
              flexWrap: 'wrap',
              alignItems: 'center',
              marginBottom: 28,
            }}
          >
            <Link
              to="/chat"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '14px 24px',
                borderRadius: 999,
                background: '#ffffff',
                color: '#0a1024',
                fontFamily: fonts.sans,
                fontWeight: 500,
                fontSize: 15,
                letterSpacing: '-0.005em',
                textDecoration: 'none',
                boxShadow: '0 10px 30px -10px rgba(179, 200, 239, 0.45), 0 6px 18px -10px rgba(0, 0, 0, 0.5)',
                transition: `transform 220ms ${ease.outQuint}, box-shadow 220ms ${ease.outQuint}`,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-1px)';
                e.currentTarget.style.boxShadow = '0 14px 36px -10px rgba(179, 200, 239, 0.6), 0 8px 22px -10px rgba(0, 0, 0, 0.65)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 10px 30px -10px rgba(179, 200, 239, 0.45), 0 6px 18px -10px rgba(0, 0, 0, 0.5)';
              }}
            >
              Start learning
              <span aria-hidden style={{ fontSize: 18, lineHeight: 1 }}>→</span>
            </Link>

            <a
              href="#features"
              onClick={scrollToFeatures}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '14px 22px',
                borderRadius: 999,
                background: 'rgba(255, 255, 255, 0.04)',
                color: 'rgba(243, 245, 250, 0.85)',
                fontFamily: fonts.sans,
                fontWeight: 500,
                fontSize: 15,
                letterSpacing: '-0.005em',
                textDecoration: 'none',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                backdropFilter: 'blur(8px)',
                WebkitBackdropFilter: 'blur(8px)',
                transition: `background 220ms ${ease.outQuint}, border-color 220ms ${ease.outQuint}`,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.10)';
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.22)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.12)';
              }}
            >
              See how it works
            </a>
          </div>

          {/* trust strip */}
          <div
            style={{
              ...stagger(4),
              display: 'flex',
              gap: 22,
              justifyContent: 'center',
              flexWrap: 'wrap',
              fontSize: 13,
              color: 'rgba(243, 245, 250, 0.55)',
              fontWeight: 400,
            }}
          >
            {TRUST.map((t) => (
              <span key={t} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <span
                  aria-hidden
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 14,
                    height: 14,
                    borderRadius: 999,
                    background: 'rgba(179, 200, 239, 0.16)',
                    color: '#b3c8ef',
                  }}
                >
                  <svg viewBox="0 0 14 14" width="9" height="9" fill="none" aria-hidden>
                    <path d="M3 7.2 6 10l5-6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
