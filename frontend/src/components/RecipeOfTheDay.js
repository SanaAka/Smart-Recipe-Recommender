import React, { useState, useEffect } from 'react';  // eslint-disable-line no-unused-vars
import { FaStar, FaClock, FaFire, FaCalendarDay, FaUsers } from 'react-icons/fa';
import { Link } from 'react-router-dom';
import api from '../utils/axios';
import { useRecipeImage } from '../utils/useRecipeImage';
import './RecipeOfTheDay.css';

function RecipeOfTheDay() {
  const [recipeOfDay, setRecipeOfDay] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRecipeOfTheDay();
  }, []);

  const loadRecipeOfTheDay = async () => {
    try {
      // Use the backend endpoint — returns the SAME recipe for ALL users today
      const response = await api.get('/api/recipe-of-the-day');

      if (response.data.recipe) {
        const r = response.data.recipe;
        setRecipeOfDay({
          id: r.id,
          name: r.name,
          description: r.description || '',
          image: r.image_url,
          cook_time: r.minutes,
          rating: r.avg_rating || 0,
          rating_count: r.rating_count || 0,
          calories: r.calories,
          tags: r.tags || []
        });
      }
    } catch (error) {
      console.error('Error loading recipe of the day:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="recipe-of-day">
        <div className="recipe-of-day-loading">
          <div className="loading-spinner-small"></div>
          <p>Loading today's featured recipe...</p>
        </div>
      </div>
    );
  }

  if (!recipeOfDay) return null;

  return <RecipeOfTheDayCard recipe={recipeOfDay} />;
}

function RecipeOfTheDayCard({ recipe }) {
  const { imageUrl, loading, containerRef, photoInfo } = useRecipeImage(recipe.id, recipe.image, { lazy: false, recipeName: recipe.name });
  const [imgLoaded, setImgLoaded] = React.useState(false);

  return (
    <div className="recipe-of-day">
      <div className="recipe-of-day-header">
        <div className="recipe-of-day-badge">
          <FaCalendarDay className="badge-icon" />
          <span>Recipe of the Day</span>
        </div>
        <p className="recipe-of-day-subtitle">
          <FaUsers style={{ fontSize: 11, opacity: 0.7 }} /> Same pick for everyone — refreshes daily
        </p>
      </div>
      
      <Link to={`/recipe/${recipe.id}`} className="recipe-of-day-content">
        <div className="recipe-of-day-image" ref={containerRef}>
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
            <div className="recipe-of-day-placeholder">
              <FaFire className="placeholder-icon" />
            </div>
          ) : null}
          <div className="recipe-of-day-overlay">
            <span className="view-recipe-btn">View Recipe →</span>
          </div>
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
        </div>

        <div className="recipe-of-day-info">
          <h3 className="recipe-of-day-title">{recipe.name}</h3>
          
          {recipe.description && (
            <p className="recipe-of-day-description">
              {recipe.description.substring(0, 150)}
              {recipe.description.length > 150 ? '...' : ''}
            </p>
          )}

          <div className="recipe-of-day-meta">
            {recipe.cook_time > 0 && (
              <div className="meta-item">
                <FaClock />
                <span>{recipe.cook_time} min</span>
              </div>
            )}
            {recipe.rating > 0 && (
              <div className="meta-item">
                <FaStar />
                <span>{recipe.rating.toFixed(1)}</span>
                {recipe.rating_count > 0 && (
                  <span className="rating-count">({recipe.rating_count})</span>
                )}
              </div>
            )}
            {recipe.calories > 0 && (
              <div className="meta-item">
                <FaFire />
                <span>{Math.round(recipe.calories)} cal</span>
              </div>
            )}
          </div>

          {recipe.tags && recipe.tags.length > 0 && (
            <div className="recipe-of-day-tags">
              {recipe.tags.slice(0, 4).map((tag, i) => (
                <span key={i} className="rotd-tag">{tag}</span>
              ))}
            </div>
          )}
        </div>
      </Link>
    </div>
  );
}

export default RecipeOfTheDay;
