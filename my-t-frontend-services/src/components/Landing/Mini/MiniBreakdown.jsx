import React from 'react';
import './Mini.css';

// Echoes real TopicBreakdown.jsx: bordered accordion rows with topic-ID chips
// and one row open showing its summary.
const ROWS = [
  { id: '1.1', title: 'Limits and continuity' },
  { id: '1.2', title: 'Rules of differentiation', open: true, summary: 'Power, product, quotient, and chain rules. How each one falls out of the limit definition.' },
  { id: '1.3', title: 'Applications: rates of change' },
];

const MiniBreakdown = () => (
  <div className="mini-frame">
    <div className="mini-header">
      <span className="mini-dots"><i /><i /><i /></span>
      Topic breakdown · Calculus
    </div>
    <div>
      {ROWS.map((r) => (
        <React.Fragment key={r.id}>
          <div className={`mini-bd-row ${r.open ? 'open' : ''}`}>
            <svg className="mini-bd-chevron" viewBox="0 0 16 16" fill="none" aria-hidden>
              <path d="M6 4 L10 8 L6 12" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="mini-bd-id">{r.id}</span>
            <span className="mini-bd-title">{r.title}</span>
          </div>
          {r.open && r.summary && (
            <div className="mini-bd-summary">{r.summary}</div>
          )}
        </React.Fragment>
      ))}
    </div>
  </div>
);

export default MiniBreakdown;
