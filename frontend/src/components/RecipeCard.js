import React from 'react';
import { Link } from 'react-router-dom';
import { FaClock, FaFire, FaHeart, FaRegHeart } from 'react-icons/fa';
import './RecipeCard.css';

function RecipeCard({ recipe, onToggleFavorite, isFavorite }) {
  const handleFavoriteClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    onToggleFavorite(recipe.id);
  };

  const imageUrl = recipe.image_url || recipe.image || recipe.imageUrl;
  const [imageError, setImageError] = React.useState(false);

  return (
    <Link to={`/recipe/${recipe.id}`} className="recipe-card">
      <div className="recipe-card-header">
        {imageUrl && !imageError ? (
          <img 
            src={imageUrl} 
            alt={recipe.name}
            className="recipe-image"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="recipe-image-placeholder">
            <FaFire className="recipe-icon" />
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
