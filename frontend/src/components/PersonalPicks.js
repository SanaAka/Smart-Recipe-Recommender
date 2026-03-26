import React, { useState, useEffect, useContext } from 'react';
import { FaStar, FaClock, FaFire, FaMagic, FaHeart, FaArrowRight } from 'react-icons/fa';
import { Link } from 'react-router-dom';
import { AuthContext } from '../App';
import api from '../utils/axios';
import { useRecipeImage } from '../utils/useRecipeImage';
import './PersonalPicks.css';

function PersonalPicks() {
  const { isAuthenticated } = useContext(AuthContext);
  const [recipes, setRecipes] = useState([]);
  const [strategy, setStrategy] = useState('');
  const [basedOnTags, setBasedOnTags] = useState([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated) {
      loadPersonalPicks();
    } else {
      setLoading(false);
    }
  }, [isAuthenticated]);

  const loadPersonalPicks = async () => {
    try {
      const response = await api.get('/api/recommendations/personal', {
        params: { limit: 6 },
        skipAuthRedirect: true
      });

      setRecipes(response.data.recipes || []);
      setStrategy(response.data.strategy || '');
      setBasedOnTags(response.data.based_on_tags || []);
      setMessage(response.data.message || '');
    } catch (error) {
      // 401 means not logged in — that's fine, just hide the section
      if (error.response?.status !== 401) {
        console.error('Error loading personal picks:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  // Don't render for unauthenticated users
  if (!isAuthenticated) return null;

  if (loading) {
    return (
      <div className="personal-picks">
        <div className="personal-picks-loading">
          <div className="loading-spinner-small"></div>
          <p>Finding recipes you'll love...</p>
        </div>
      </div>
    );
  }

  if (recipes.length === 0) return null;

  return (
    <div className="personal-picks">
      <div className="personal-picks-header">
        <div className="personal-picks-badge">
          <FaMagic className="badge-icon" />
          <span>Picked for You</span>
        </div>
        {strategy === 'personalized' && basedOnTags.length > 0 && (
          <p className="personal-picks-subtitle">
            Based on your love for{' '}
            {basedOnTags.slice(0, 3).map((tag, i) => (
              <span key={i} className="highlight-tag">
                {tag}{i < Math.min(basedOnTags.length, 3) - 1 ? ', ' : ''}
              </span>
            ))}
          </p>
        )}
        {strategy === 'top-rated' && message && (
          <p className="personal-picks-subtitle">
            <FaHeart style={{ fontSize: 11, color: 'var(--accent-500)' }} />{' '}
            {message}
          </p>
        )}
      </div>

      <div className="personal-picks-grid">
        {recipes.map((recipe) => (
          <PickCard key={recipe.id} recipe={recipe} />
        ))}
      </div>
    </div>
  );
}

function PickCard({ recipe }) {
  const { imageUrl, loading, containerRef } = useRecipeImage(recipe.id, recipe.image_url, { recipeName: recipe.name });
  const [imgLoaded, setImgLoaded] = React.useState(false);

  return (
    <Link to={`/recipe/${recipe.id}`} className="personal-pick-card">
      <div className="pick-card-image" ref={containerRef}>
        {(loading || (imageUrl && !imgLoaded)) && <div className="image-shimmer" />}
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={recipe.name}
            loading="lazy"
            className={imgLoaded ? 'img-loaded' : 'img-loading'}
            onLoad={() => setImgLoaded(true)}
          />
        ) : !loading ? (
          <div className="pick-card-placeholder">
            <FaFire />
          </div>
        ) : null}
      </div>
      <div className="pick-card-info">
        <h4 className="pick-card-title">{recipe.name}</h4>
        <div className="pick-card-meta">
          {recipe.minutes > 0 && (
            <span className="pick-meta-item">
              <FaClock /> {recipe.minutes}m
            </span>
          )}
          {recipe.calories > 0 && (
            <span className="pick-meta-item">
              <FaFire /> {Math.round(recipe.calories)} cal
            </span>
          )}
          {recipe.avg_rating > 0 && (
            <span className="pick-meta-item">
              <FaStar /> {recipe.avg_rating}
            </span>
          )}
        </div>
        {recipe.tags && recipe.tags.length > 0 && (
          <div className="pick-card-tags">
            {recipe.tags.slice(0, 2).map((tag, i) => (
              <span key={i} className="pick-tag">{tag}</span>
            ))}
          </div>
        )}
      </div>
      <div className="pick-card-arrow">
        <FaArrowRight />
      </div>
    </Link>
  );
}

export default PersonalPicks;
