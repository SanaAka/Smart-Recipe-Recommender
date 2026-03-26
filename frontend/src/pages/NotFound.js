import React from 'react';
import { Link } from 'react-router-dom';
import { FaHome, FaSearch, FaExclamationTriangle } from 'react-icons/fa';
import './NotFound.css';

function NotFound() {
  return (
    <div className="not-found-page">
      <div className="not-found-content">
        <FaExclamationTriangle className="not-found-icon" />
        <h1 className="not-found-code">404</h1>
        <h2 className="not-found-title">Page Not Found</h2>
        <p className="not-found-message">
          Oops! The recipe you're looking for seems to have gone missing from the kitchen.
        </p>
        <div className="not-found-actions">
          <Link to="/" className="btn btn-primary">
            <FaHome /> Go Home
          </Link>
          <Link to="/search" className="btn btn-secondary">
            <FaSearch /> Search Recipes
          </Link>
        </div>
      </div>
    </div>
  );
}

export default NotFound;
