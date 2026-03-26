import React from 'react';
import { Link } from 'react-router-dom';
import { FaClock, FaFire, FaHeart, FaRegHeart } from 'react-icons/fa';
import { useRecipeImage } from '../utils/useRecipeImage';
import './RecipeCard.css';

function RecipeCard({ recipe, onToggleFavorite, isFavorite }) {
  const handleFavoriteClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    onToggleFavorite(recipe.id);
  };

  const rawUrl = recipe.image_url || recipe.image || recipe.imageUrl;
  const { imageUrl, loading, containerRef, photoInfo } = useRecipeImage(recipe.id, rawUrl, { recipeName: recipe.name });
  const [imageLoaded, setImageLoaded] = React.useState(false);
  const [imageError, setImageError] = React.useState(false);

  return (
    <Link to={`/recipe/${recipe.id}`} className="recipe-card">
      <div className="recipe-card-header" ref={containerRef}>
        {/* Shimmer skeleton — visible while image is loading */}
        {(loading || (imageUrl && !imageLoaded && !imageError)) && (
          <div className="image-shimmer" />
        )}

        {imageUrl && !imageError ? (
          <img 
            src={imageUrl} 
            alt={recipe.name}
            className={`recipe-image ${imageLoaded ? 'loaded' : 'loading'}`}
            loading="lazy"
            onLoad={() => setImageLoaded(true)}
            onError={() => setImageError(true)}
          />
        ) : !loading ? (
          <div className="recipe-image-placeholder">
            <svg className="food-placeholder-icon" viewBox="0 0 64 64" fill="none">
              <circle cx="32" cy="32" r="28" stroke="currentColor" strokeWidth="2" opacity="0.3"/>
              <path d="M20 28c0-6.627 5.373-12 12-12s12 5.373 12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.4"/>
              <ellipse cx="32" cy="36" rx="16" ry="8" stroke="currentColor" strokeWidth="2" opacity="0.3"/>
              <path d="M18 36c0 4 6 12 14 12s14-8 14-12" stroke="currentColor" strokeWidth="2" opacity="0.3"/>
              <circle cx="26" cy="32" r="2" fill="currentColor" opacity="0.25"/>
              <circle cx="32" cy="30" r="2" fill="currentColor" opacity="0.25"/>
              <circle cx="38" cy="32" r="2" fill="currentColor" opacity="0.25"/>
            </svg>
          </div>
        ) : null}

        {/* Unsplash attribution (required by API guidelines) */}
        {photoInfo && photoInfo.photographer && (
          <div className="unsplash-attribution" onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}>
            Photo by{' '}
            <span className="unsplash-attr-link" onClick={(e) => { e.preventDefault(); e.stopPropagation(); window.open(photoInfo.photographer_url, '_blank'); }}>
              {photoInfo.photographer}
            </span>
            {' '}on{' '}
            <span className="unsplash-attr-link" onClick={(e) => { e.preventDefault(); e.stopPropagation(); window.open(photoInfo.unsplash_url, '_blank'); }}>
              Unsplash
            </span>
          </div>
        )}

        <button 
          className={`favorite-btn ${isFavorite ? 'favorited' : ''}`}
          onClick={handleFavoriteClick}
        >
          {isFavorite ? <FaHeart /> : <FaRegHeart />}
        </button>
      </div>
      
      <div className="recipe-card-body">
        <h3 className="recipe-title">{recipe.name}</h3>
        
        <div className="recipe-meta">
          {recipe.minutes && (
            <div className="meta-item">
              <FaClock />
              <span>{recipe.minutes} min</span>
            </div>
          )}
          {recipe.calories && (
            <div className="meta-item">
              <FaFire />
              <span>{Math.round(recipe.calories)} cal</span>
            </div>
          )}
        </div>

        {recipe.tags && recipe.tags.length > 0 && (
          <div className="recipe-tags">
            {recipe.tags.slice(0, 3).map((tag, index) => (
              <span key={index} className="tag">{tag}</span>
            ))}
          </div>
        )}

        {recipe.ingredients && (
          <p className="recipe-ingredients-preview">
            {recipe.ingredients.slice(0, 3).join(', ')}
            {recipe.ingredients.length > 3 && '...'}
          </p>
        )}
      </div>
    </Link>
  );
}

// Memoize to avoid unnecessary re-renders in large lists
export default React.memo(RecipeCard, (prev, next) => {
  if (prev.isFavorite !== next.isFavorite) return false;
  const pr = prev.recipe || {};
  const nr = next.recipe || {};
  if (pr.id !== nr.id) return false;
  if (pr.name !== nr.name) return false;
  if (pr.minutes !== nr.minutes) return false;
  const pc = Math.round(pr.calories || 0);
  const nc = Math.round(nr.calories || 0);
  if (pc !== nc) return false;
  const pTags = (pr.tags || []).slice(0, 3).join('|');
  const nTags = (nr.tags || []).slice(0, 3).join('|');
  if (pTags !== nTags) return false;
  const pIngs = (pr.ingredients || []).slice(0, 3).join('|');
  const nIngs = (nr.ingredients || []).slice(0, 3).join('|');
  return pIngs === nIngs;
});
