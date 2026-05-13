import React, { useEffect, useState } from 'react';
import './Mini.css';

const ANSWER =
  'The author argues attention does away with recurrence entirely. Sequence dependencies are modeled by query and key dot products across every position in parallel.';

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const MiniDocQA = () => {
  const words = ANSWER.split(' ');
  const [shown, setShown] = useState(prefersReducedMotion() ? words.length : 0);

  useEffect(() => {
    if (prefersReducedMotion()) return undefined;
    let i = 0;
    let timer;
    const tick = () => {
      i = (i + 1) % (words.length + 12);
      setShown(Math.min(i, words.length));
      timer = setTimeout(tick, i === 0 ? 700 : 95);
    };
    timer = setTimeout(tick, 500);
    return () => clearTimeout(timer);
  }, [words.length]);

  const text = words.slice(0, shown).join(' ');

  return (
    <div className="mini-frame">
      <div className="mini-header">
        <span className="mini-dots"><i /><i /><i /></span>
        Reading with you
      </div>
      <span className="mini-doc-pill">
        <svg viewBox="0 0 16 16" fill="none">
          <path d="M3.5 2h6L13 5.5V14H3.5V2Z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
          <path d="M9.5 2v3.5H13" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
        </svg>
        attention-is-all-you-need.pdf
      </span>
      <div className="mini-doc-q">What is the core claim of section 3?</div>
      <div className="mini-doc-a">
        {text}
        {shown < words.length && <span className="mini-cursor" style={{ background: '#1d2230' }} />}
      </div>
    </div>
  );
};

export default MiniDocQA;
