import React from 'react';
import './Mini.css';

const MiniStudyPlan = () => (
  <div className="mini-frame mini-sp">
    <div className="mini-sp-card">
      <div className="mini-sp-top">
        <div className="mini-sp-day">
          Day 1 <small>· Mon, May 14</small>
          <span className="mini-sp-prio">High</span>
        </div>
        <span className="mini-sp-duration">2 hours</span>
      </div>

      <div className="mini-sp-label">Topics</div>
      <div className="mini-sp-chips">
        <span className="mini-sp-chip">Linear regression</span>
        <span className="mini-sp-chip">OLS assumptions</span>
        <span className="mini-sp-chip">Residuals</span>
      </div>

      <div className="mini-sp-label">Activities</div>
      <ul className="mini-sp-list">
        <li>Read chapter 4, sections 4.1 to 4.3.</li>
        <li>Work through problems 1 to 8 in the workbook.</li>
      </ul>
    </div>
  </div>
);

export default MiniStudyPlan;
