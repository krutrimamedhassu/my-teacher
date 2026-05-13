import React, { useEffect, useState } from 'react';
import './Mini.css';

const QUESTION = 'Can you explain the bias variance tradeoff like I’m a junior?';
const ANSWER =
  'Think of it as two ways a model can be wrong. Too rigid, and it misses real patterns. Too jumpy, and it memorizes noise. The trick is sitting in the middle: flexible enough to learn, calm enough to generalize.';

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const MiniChat = () => {
  const words = ANSWER.split(' ');
  const [shown, setShown] = useState(prefersReducedMotion() ? words.length : 0);

  useEffect(() => {
    if (prefersReducedMotion()) return undefined;
    let i = 0;
    let timer;
    const tick = () => {
      i = (i + 1) % (words.length + 14); // hold full message, then loop
      setShown(Math.min(i, words.length));
      timer = setTimeout(tick, i === 0 ? 600 : 90);
    };
    timer = setTimeout(tick, 400);
    return () => clearTimeout(timer);
  }, [words.length]);

  const text = words.slice(0, shown).join(' ');

  return (
    <div className="mini-frame" style={{ minHeight: 220 }}>
      <div className="mini-header">
        <span className="mini-dots"><i /><i /><i /></span>
        Conversation
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div className="mini-chat-bubble user">{QUESTION}</div>
        <div className="mini-chat-bubble tutor">
          {text}
          {shown < words.length && <span className="mini-cursor" />}
        </div>
      </div>
    </div>
  );
};

export default MiniChat;
