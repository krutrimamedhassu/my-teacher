import React from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, ListTree, Mic } from 'lucide-react';
import { useReveal, revealStyle } from './useReveal';
import './Landing.css';

const TILES = [
  {
    icon: Sparkles,
    title: 'Key concepts',
    body: 'Pull out the ideas you really need to know, before you study the rest.',
  },
  {
    icon: ListTree,
    title: 'Topic breakdowns',
    body: 'Break a subject into small parts you can learn one at a time.',
  },
  {
    icon: Mic,
    title: 'Speak & listen',
    body: 'Talk to your tutor and hear answers read back. Handy when your eyes need a break.',
  },
];

const FeatureGridLite = () => {
  const { ref, visible } = useReveal();
  return (
    <div ref={ref} style={revealStyle(visible)}>
      <div className="gridlite-divider"><span>And more in the toolkit</span></div>
      <div className="gridlite-shell">
        <div className="gridlite">
          {TILES.map((t) => {
            const Icon = t.icon;
            return (
              <Link
                key={t.title}
                to="/chat"
                className="gridlite-tile"
                style={{ textDecoration: 'none', color: 'inherit' }}
              >
                <span className="gridlite-icon">
                  <Icon size={20} strokeWidth={1.8} />
                </span>
                <h4>{t.title}</h4>
                <p>{t.body}</p>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default FeatureGridLite;
