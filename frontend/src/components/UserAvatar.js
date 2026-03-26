import React from 'react';
import './UserAvatar.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

/**
 * Reusable avatar component.
 * Shows profile picture if available, otherwise a letter avatar.
 *
 * Props:
 *  - username (string, required)
 *  - profilePic (string|null) – URL path like "/api/uploads/profile_pics/xxx.jpg"
 *  - size ("sm" | "md" | "lg" | "xl")  default "md"
 *  - className (string) – extra classes
 */
function UserAvatar({ username, profilePic, size = 'md', className = '' }) {
  const letter = username ? username[0].toUpperCase() : '?';
  const src = profilePic ? `${API_BASE}${profilePic}` : null;

  return (
    <span className={`user-avatar user-avatar-${size} ${className}`}>
      {src ? (
        <img
          src={src}
          alt={`${username}'s avatar`}
          className="user-avatar-img"
          onError={(e) => {
            // Fallback to letter on load error
            e.target.style.display = 'none';
            e.target.nextSibling.style.display = 'flex';
          }}
        />
      ) : null}
      <span
        className="user-avatar-letter"
        style={src ? { display: 'none' } : undefined}
      >
        {letter}
      </span>
    </span>
  );
}

export default UserAvatar;
