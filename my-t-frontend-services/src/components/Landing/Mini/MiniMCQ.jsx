import React, { useEffect, useState } from 'react';
import './Mini.css';

const Q = 'In gradient descent, what does the learning rate primarily control?';
const OPTS = [
  'The size of each weight update',
  'The number of training examples',
  'The depth of the model',
  'The loss function used',
];
const CORRECT = 0;

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// 0: nothing selected, 1: option B selected, 2: switched to A (correct one),
// 3: submitted -> correct revealed
const STEPS = 4;

const MiniMCQ = () => {
  const [step, setStep] = useState(prefersReducedMotion() ? 3 : 0);

  useEffect(() => {
    if (prefersReducedMotion()) return undefined;
    const id = setInterval(() => {
      setStep((s) => (s + 1) % (STEPS + 2));
    }, 1500);
    return () => clearInterval(id);
  }, []);

  const s = Math.min(step, STEPS - 1);
  const selected = s === 1 ? 1 : s >= 2 ? 0 : null;
  const revealed = s >= 3;
  const submitted = revealed;

  return (
    <div className="mini-frame">
      <div className="mini-header">
        <span className="mini-dots"><i /><i /><i /></span>
        Quiz · Question 4
      </div>
      <div className="mini-mcq-q">{Q}</div>
      <div>
        {OPTS.map((text, i) => {
          const isSelected = selected === i && !revealed;
          const isCorrect = revealed && i === CORRECT;
          const cls = [
            'mini-mcq-opt',
            isSelected ? 'selected' : '',
            isCorrect ? 'correct' : '',
          ].filter(Boolean).join(' ');
          return (
            <div className={cls} key={text}>
              <span className="mini-mcq-radio" aria-hidden />
              <span>{text}</span>
              <svg className="mini-mcq-check" viewBox="0 0 16 16" fill="none" aria-hidden>
                <path d="M3 8.5 6.5 12 13 4.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
          );
        })}
      </div>
      <div className="mini-mcq-actions">
        <button type="button" className={`mini-mcq-submit ${submitted ? 'done' : ''}`}>
          {submitted ? 'Submitted' : 'Submit'}
        </button>
      </div>
    </div>
  );
};

export default MiniMCQ;
