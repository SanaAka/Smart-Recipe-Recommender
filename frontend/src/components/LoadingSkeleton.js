import React from 'react';
import './LoadingSkeleton.css';

function LoadingSkeleton({ count = 6 }) {
  return (
    <div className="recipe-grid">
      {[...Array(count)].map((_, index) => (
        <div key={index} className="skeleton-card">
          <div className="skeleton-header"></div>
          <div className="skeleton-body">
            <div className="skeleton-title"></div>
            <div className="skeleton-meta">
              <div className="skeleton-meta-item"></div>
              <div className="skeleton-meta-item"></div>
            </div>
            <div className="skeleton-text"></div>
            <div className="skeleton-text"></div>
            <div className="skeleton-text short"></div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default LoadingSkeleton;
