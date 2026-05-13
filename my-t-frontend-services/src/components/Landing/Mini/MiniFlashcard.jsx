import React, { useEffect, useState } from 'react';
import './Mini.css';

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const MiniFlashcard = () => {
  const [flipped, setFlipped] = useState(false);

  useEffect(() => {
    if (prefersReducedMotion()) return undefined;
    const id = setInterval(() => setFlipped((v) => !v), 4200);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="mini-frame">
      <div className={`mini-fc ${flipped ? 'flipped' : ''}`}>
        <div className="mini-fc-inner">
          <div className="mini-fc-face">
            <div className="mini-fc-header">
              <span className="mini-fc-ribbon">Biology</span>
              <span className="mini-fc-pill">Medium</span>
            </div>
            <div className="mini-fc-body">
              What does the mitochondrion do for the cell?
            </div>
          </div>
          <div className="mini-fc-face back">
            <div className="mini-fc-header">
              <span className="mini-fc-ribbon">Answer</span>
              <span className="mini-fc-pill">Medium</span>
            </div>
            <div className="mini-fc-body">
              Produces most of the cell’s energy by generating ATP through cellular respiration.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MiniFlashcard;
