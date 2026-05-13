import React from 'react';
import './Mini.css';

// Echoes real VisualFlowchart.jsx: typed nodes (start = pill, process = rounded,
// decision = dashed rounded), dashed animated connectors with arrowheads,
// Yes/No labels at the decision split.
const MiniFlowchart = () => (
  <div className="mini-frame">
    <div className="mini-header">
      <span className="mini-dots"><i /><i /><i /></span>
      Visual explanation
    </div>
    <svg viewBox="0 0 380 280" className="mini-fl-svg">
      <defs>
        <marker id="miniFlArrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M0 0 L10 5 L0 10 z" className="mini-fl-arrow" />
        </marker>
      </defs>

      {/* connectors */}
      <path className="mini-fl-line" d="M190 38 L190 70" markerEnd="url(#miniFlArrow)" />
      <path className="mini-fl-line" d="M190 110 L190 138" markerEnd="url(#miniFlArrow)" />
      <path className="mini-fl-line" d="M190 188 L96 224" markerEnd="url(#miniFlArrow)" />
      <path className="mini-fl-line" d="M190 188 L284 224" markerEnd="url(#miniFlArrow)" />

      {/* Yes/No labels */}
      <text x="116" y="208" textAnchor="middle" className="mini-fl-yn" fill="#1f7a4e">Yes</text>
      <text x="260" y="208" textAnchor="middle" className="mini-fl-yn" fill="#b34a3a">No</text>

      {/* start (round pill) */}
      <g>
        <rect x="142" y="14" width="96" height="28" rx="14" fill="#0a1024" />
        <text x="190" y="33" textAnchor="middle" className="mini-fl-text inv">Start</text>
      </g>

      {/* process (rounded card) */}
      <g>
        <rect x="124" y="74" width="132" height="40" rx="10" fill="#ffffff" stroke="rgba(20,30,60,0.16)" />
        <text x="190" y="92" textAnchor="middle" className="mini-fl-text">Train model</text>
        <text x="190" y="106" textAnchor="middle" className="mini-fl-text" style={{ opacity: 0.55, fontSize: 10 }}>(epoch step)</text>
      </g>

      {/* decision (dashed border) */}
      <g>
        <rect x="118" y="142" width="144" height="48" rx="8" fill="#ffffff" stroke="rgba(20,30,60,0.6)" strokeWidth="2" strokeDasharray="5 5" />
        <text x="190" y="164" textAnchor="middle" className="mini-fl-text">Accuracy &gt; 90%?</text>
        <text x="190" y="180" textAnchor="middle" className="mini-fl-text" style={{ opacity: 0.55, fontSize: 10 }}>(validation)</text>
      </g>

      {/* end pills */}
      <g>
        <rect x="38" y="228" width="116" height="32" rx="16" fill="#1f7a4e" />
        <text x="96" y="248" textAnchor="middle" className="mini-fl-text inv">Predict</text>
      </g>
      <g>
        <rect x="226" y="228" width="116" height="32" rx="16" fill="#0a1024" />
        <text x="284" y="248" textAnchor="middle" className="mini-fl-text inv">Tune &amp; retry</text>
      </g>
    </svg>
  </div>
);

export default MiniFlowchart;
