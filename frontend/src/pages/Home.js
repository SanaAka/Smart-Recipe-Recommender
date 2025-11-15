import React, { useState, useEffect } from 'react';
import { FaSearch, FaUtensils } from 'react-icons/fa';
import axios from 'axios';
import RecipeCard from '../components/RecipeCard';
import LoadingSkeleton from '../components/LoadingSkeleton';
import './Home.css';

function Home() {
  const [ingredients, setIngredients] = useState('');
  const [dietaryPreference, setDietaryPreference] = useState('');
  const [cuisineType, setCuisineType] = useState('');
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [favorites, setFavorites] = useState([]);

  useEffect(() => {
    loadFavorites();
  }, []);

  const loadFavorites = () => {
    const savedFavorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    setFavorites(savedFavorites);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setRecommendations([]);

    try {
      const response = await axios.post('/api/recommend', {
        ingredients: ingredients.split(',').map(i => i.trim()).filter(i => i),
        dietary_preference: dietaryPreference,
        cuisine_type: cuisineType
      });

      // Check if ML model is still loading
      if (response.status === 202 || response.data.loading) {
        setError('🤖 AI is warming up... Try searching instead, or wait a few seconds and try again!');
        setLoading(false);
        return;
      }

      setRecommendations(response.data.recommendations || []);
      
      if (response.data.recommendations.length === 0) {
        setError('No recipes found matching your criteria. Try different ingredients or preferences.');
      }
    } catch (err) {
      if (err.response?.status === 202) {
        setError('🤖 AI is warming up... Try searching instead, or wait a few seconds and try again!');
      } else {
        setError(err.response?.data?.error || 'Failed to get recommendations. Please try again.');
      }
      console.error('Error getting recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleFavorite = (recipeId) => {
    const savedFavorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    let newFavorites;

    if (savedFavorites.includes(recipeId)) {
      newFavorites = savedFavorites.filter(id => id !== recipeId);
    } else {
      newFavorites = [...savedFavorites, recipeId];
    }

    localStorage.setItem('favorites', JSON.stringify(newFavorites));
    setFavorites(newFavorites);
  };

  return (
    <div className="home-page">
      <div className="hero-section">
        <div className="container">
          <div className="hero-content">
            <h1 className="hero-title">
              <FaUtensils className="hero-icon" />
              Discover Your Perfect Recipe
            </h1>
            <p className="hero-subtitle">
              Get personalized recipe recommendations based on your available ingredients and preferences
            </p>
          </div>

          <form className="search-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="ingredients">Available Ingredients</label>
              <input
                id="ingredients"
                type="text"
                className="input"
                placeholder="e.g., chicken, tomatoes, garlic (comma separated)"
                value={ingredients}
                onChange={(e) => setIngredients(e.target.value)}
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="dietary">Dietary Preference</label>
                <select
                  id="dietary"
                  className="select"
                  value={dietaryPreference}
                  onChange={(e) => setDietaryPreference(e.target.value)}
                >
                  <option value="">Any</option>
                  <option value="vegetarian">Vegetarian</option>
                  <option value="vegan">Vegan</option>
                  <option value="low-carb">Low Carb</option>
                  <option value="keto">Keto</option>
                  <option value="gluten-free">Gluten Free</option>
                  <option value="dairy-free">Dairy Free</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="cuisine">Cuisine Type</label>
                <select
                  id="cuisine"
                  className="select"
                  value={cuisineType}
                  onChange={(e) => setCuisineType(e.target.value)}
                >
                  <option value="">Any</option>
                  <option value="italian">Italian</option>
                  <option value="mexican">Mexican</option>
                  <option value="chinese">Chinese</option>
                  <option value="indian">Indian</option>
                  <option value="japanese">Japanese</option>
                  <option value="french">French</option>
                  <option value="greek">Greek</option>
                  <option value="spanish">Spanish</option>
                  <option value="american">American</option>
                  <option value="mediterranean">Mediterranean</option>
                  <option value="korean">Korean</option>
                  <option value="vietnamese">Vietnamese</option>
                  <option value="middle eastern">Middle Eastern</option>
                  <option value="caribbean">Caribbean</option>
                  <option value="asian fusion">Asian Fusion</option>
                </select>
              </div>
            </div>

            <button type="submit" className="btn btn-primary submit-btn" disabled={loading}>
              <FaSearch />
              {loading ? 'Searching...' : 'Get Recommendations'}
            </button>
          </form>
        </div>
      </div>

      <div className="results-section">
        <div className="container">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {loading && (
            <LoadingSkeleton count={12} />
          )}

          {recommendations.length > 0 && !loading && (
            <>
              <h2 className="section-title">Recommended Recipes for You</h2>
              <div className="recipe-grid">
                {recommendations.map((recipe) => (
                  <RecipeCard
                    key={recipe.id}
                    recipe={recipe}
                    isFavorite={favorites.includes(recipe.id)}
                    onToggleFavorite={toggleFavorite}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default Home;
