import React, { useState, useEffect, useRef } from 'react';
import { FaHeart, FaTrash } from 'react-icons/fa';
import api from '../utils/axios';
import RecipeCard from '../components/RecipeCard';
import LoadingSkeleton from '../components/LoadingSkeleton';
import { useToast } from '../context/ToastContext';
import { useConfirm } from '../context/ConfirmContext';
import { useFavorites } from '../context/FavoritesContext';
import './Favorites.css';

function Favorites() {
  const { toast } = useToast();
  const { confirm } = useConfirm();
  const { favorites, removeFavorite, clearAllFavorites: ctxClearAll } = useFavorites();
  const [favoriteRecipes, setFavoriteRecipes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const hasFetchedRef = useRef(false);
  const prevFavLenRef = useRef(-1);

  useEffect(() => {
    // Fetch recipe details when favorites change
    if (favorites.length === 0) {
      setFavoriteRecipes([]);
      prevFavLenRef.current = 0;
      return;
    }
    // Only re-fetch if the count changed (not on every render)
    if (prevFavLenRef.current === favorites.length && hasFetchedRef.current) return;
    prevFavLenRef.current = favorites.length;
    hasFetchedRef.current = true;
    loadRecipeDetails();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [favorites]);

  const loadRecipeDetails = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await api.post('/api/recipes/batch', {
        recipe_ids: favorites
      });

      setFavoriteRecipes(response.data.recipes || []);
    } catch (err) {
      setError('Failed to load favorite recipes. Please try again.');
      console.error('Error loading favorites:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = (recipeId) => {
    removeFavorite(recipeId);
    setFavoriteRecipes(prev => prev.filter(r => r.id !== recipeId));
  };

  const handleClearAll = async () => {
    const ok = await confirm({
      title: 'Clear All Favorites',
      message: `Remove all ${favorites.length} saved recipes from your favorites?`,
      confirmText: 'Clear All',
      cancelText: 'Keep them',
      variant: 'danger',
    });
    if (!ok) return;

    ctxClearAll();
    setFavoriteRecipes([]);
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
              onClick={handleClearAll}
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
                onToggleFavorite={handleRemove}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Favorites;
