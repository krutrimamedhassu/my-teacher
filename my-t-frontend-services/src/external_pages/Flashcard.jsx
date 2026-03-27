import React, { useState } from 'react';
import './Flashcard.css';

export default function Flashcard({ question, answer, subject, difficulty, style }) {
  const [flipped, setFlipped] = useState(false);

  return (
    <div
      className={`flashcard ${flipped ? 'flipped' : ''}`}
      onClick={() => setFlipped(!flipped)}
      style={style}
    >
      <div className="card-inner">
        {/* FRONT */}
        <div className="card-face card-front">
          <div className="card-header">
            <span className="ribbon subject">{subject}</span>
            <span className={`pill difficulty ${difficulty.toLowerCase()}`}>
              {difficulty}
            </span>
          </div>
          <div className="card-body">
            <p>{question}</p>
          </div>
        </div>
        {/* BACK */}
        <div className="card-face card-back">
          <div className="card-header">
            <span className="ribbon answer">Answer</span>
          </div>
          <div className="card-body">
            <p>{answer}</p>
          </div>
        </div>
      </div>
    </div>
  );
}