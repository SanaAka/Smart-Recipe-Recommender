import React, { useState } from 'react';
import './StarRating.css';

const StarRating = ({ value = 0, count = 0, userRating = null, onRate, onRemove, readOnly = false, size = 'medium' }) => {
  const [hoverRating, setHoverRating] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleClick = async (rating) => {
    if (readOnly || isSubmitting || !onRate) return;
    
    setIsSubmitting(true);
    try {
      await onRate(rating);
    } catch (error) {
      console.error('Rating failed:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRemove = async () => {
    if (readOnly || isSubmitting || !onRemove) return;

    setIsSubmitting(true);
    try {
      await onRemove();
    } catch (error) {
      console.error('Remove rating failed:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleMouseEnter = (rating) => {
    if (!readOnly) setHoverRating(rating);
  };

  const handleMouseLeave = () => {
    setHoverRating(0);
  };

  const displayRating = hoverRating || value;

  return (
    <div className={`star-rating ${size} ${readOnly ? 'readonly' : 'interactive'}`}>
      <div className="stars-container">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            className={`star ${star <= displayRating ? 'filled' : 'empty'} ${
              isSubmitting ? 'submitting' : ''
            }`}
            onClick={() => handleClick(star)}
            onMouseEnter={() => handleMouseEnter(star)}
            onMouseLeave={handleMouseLeave}
            disabled={readOnly || isSubmitting}
            aria-label={`Rate ${star} star${star > 1 ? 's' : ''}`}
          >
            ★
          </button>
        ))}
      </div>
      <div className="rating-meta">
        {count > 0 && (
          <span className="rating-info">
            {value.toFixed(1)} ({count} {count === 1 ? 'rating' : 'ratings'})
          </span>
        )}
        {userRating != null && (
          <span className="user-rating-label">
           rating: {userRating}★
            <button
              type="button"
              className="remove-rating-btn"
              onClick={handleRemove}
              disabled={isSubmitting}
              title="Remove your rating"
              aria-label="Remove your rating"
            >
              ✕
            </button>
          </span>
        )}
      </div>
    </div>
  );
};

export default StarRating;
