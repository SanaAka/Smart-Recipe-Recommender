import React, { useState, useEffect, useRef } from 'react';
import { FaHeart, FaTrash } from 'react-icons/fa';
import axios from 'axios';
import RecipeCard from '../components/RecipeCard';
import LoadingSkeleton from '../components/LoadingSkeleton';
import './Favorites.css';

function Favorites() {
  const [favorites, setFavorites] = useState([]);
  const [favoriteRecipes, setFavoriteRecipes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const hasFetchedRef = useRef(false);

  useEffect(() => {
    // Prevent duplicate calls in React StrictMode
    if (!hasFetchedRef.current) {
      hasFetchedRef.current = true;
      loadFavorites();
    }
  }, []);

  const loadFavorites = async () => {
    const savedFavorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    setFavorites(savedFavorites);

    if (savedFavorites.length === 0) {
      setFavoriteRecipes([]);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/recipes/batch', {
        recipe_ids: savedFavorites
      });

      setFavoriteRecipes(response.data.recipes || []);
    } catch (err) {
      setError('Failed to load favorite recipes. Please try again.');
      console.error('Error loading favorites:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleFavorite = (recipeId) => {
    const savedFavorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    const newFavorites = savedFavorites.filter(id => id !== recipeId);
    
    localStorage.setItem('favorites', JSON.stringify(newFavorites));
    setFavorites(newFavorites);
    setFavoriteRecipes(favoriteRecipes.filter(recipe => recipe.id !== recipeId));
  };

  const clearAllFavorites = () => {
    if (window.confirm('Are you sure you want to remove all favorites?')) {
      localStorage.setItem('favorites', JSON.stringify([]));
      setFavorites([]);
      setFavoriteRecipes([]);
    }
  };

  return (
    <div className="favorites-page">
      <div className="container">
        <div className="favorites-header">
          <div className="header-content-wrapper">
            <FaHeart className="page-icon" />
            <div>
              <h1 className="page-title">My Favorite Recipes</h1>
              <p className="page-subtitle">
                {favorites.length} saved recipe{favorites.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
          
          {favorites.length > 0 && (
            <button 
              className="btn btn-danger clear-btn"
              onClick={clearAllFavorites}
            >
              <FaTrash />
              Clear All
            </button>
          )}
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {loading && (
          <LoadingSkeleton count={6} />
        )}

        {!loading && favorites.length === 0 && (
          <div className="empty-state">
            <FaHeart className="empty-icon" />
            <h2>No favorites yet</h2>
            <p>Start exploring recipes and save your favorites here!</p>
          </div>
        )}

        {!loading && favoriteRecipes.length > 0 && (
          <div className="recipe-grid">
            {favoriteRecipes.map((recipe) => (
              <RecipeCard
                key={recipe.id}
                recipe={recipe}
                isFavorite={true}
                onToggleFavorite={toggleFavorite}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Favorites;
