import React, { useState, useEffect, useRef, useCallback } from 'react';
import { FaSearch } from 'react-icons/fa';
import axios from 'axios';
import RecipeCard from '../components/RecipeCard';
import LoadingSkeleton from '../components/LoadingSkeleton';
import AdvancedFilters from '../components/AdvancedFilters';
import './Search.css';

function Search() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState('name');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [favorites, setFavorites] = useState([]);
  const [filters, setFilters] = useState({
    maxTime: '',
    maxCalories: '',
    maxIngredients: '',
    minIngredients: ''
  });
  const abortRef = useRef(null);
  const lastParamsRef = useRef('');

  useEffect(() => {
    loadFavorites();
  }, []);

  const loadFavorites = () => {
    const savedFavorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    setFavorites(savedFavorites);
  };

  const handleSearch = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!searchQuery.trim()) {
      setError('Please enter a search term');
      return;
    }

    setLoading(true);
    setError('');
    setResults([]);

    try {
      const params = {
        query: searchQuery,
        type: searchType,
        limit: 50
      };

      // Add filters if they have values
      if (filters.maxTime) params.max_time = filters.maxTime;
      if (filters.maxCalories) params.max_calories = filters.maxCalories;
      if (filters.maxIngredients) params.max_ingredients = filters.maxIngredients;
      if (filters.minIngredients) params.min_ingredients = filters.minIngredients;

      // Avoid duplicate identical requests
      const paramsKey = JSON.stringify(params);
      if (paramsKey === lastParamsRef.current) {
        setLoading(false);
        return;
      }
      lastParamsRef.current = paramsKey;

      // Cancel any in-flight request
      if (abortRef.current) {
        abortRef.current.abort();
      }
      const controller = new AbortController();
      abortRef.current = controller;

      const response = await axios.get('/api/search', { params, signal: controller.signal });

      setResults(response.data.results || []);
      
      if (response.data.results.length === 0) {
        setError('No recipes found. Try a different search term.');
      }
    } catch (err) {
      if (axios.isCancel?.(err)) {
        // Swallow cancellations
        return;
      }
      setError(err.response?.data?.error || (err.name === 'CanceledError' ? '' : 'Failed to search recipes. Please try again.'));
      console.error('Error searching recipes:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleFavorite = useCallback((recipeId) => {
    const savedFavorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    let newFavorites;

    if (savedFavorites.includes(recipeId)) {
      newFavorites = savedFavorites.filter(id => id !== recipeId);
    } else {
      newFavorites = [...savedFavorites, recipeId];
    }

    localStorage.setItem('favorites', JSON.stringify(newFavorites));
    setFavorites(newFavorites);
  }, []);

  const handleApplyFilters = (newFilters) => {
    setFilters(newFilters);
    // If there's an active search, re-run it with the new filters
    if (searchQuery.trim()) {
      handleSearch({ preventDefault: () => {} });
    }
  };

  return (
    <div className="search-page">
      <div className="container">
        <div className="search-header">
          <h1 className="page-title">Search Recipes</h1>
          <p className="page-subtitle">Find recipes by name, ingredient, or cuisine</p>
        </div>

        <div className="search-section">
          <form className="search-form-horizontal" onSubmit={handleSearch}>
            <div className="search-input-group">
              <label htmlFor="searchType" className="sr-only">Search Type</label>
              <select
                id="searchType"
                name="searchType"
                className="search-type-select"
                value={searchType}
                onChange={(e) => setSearchType(e.target.value)}
                aria-label="Search type"
              >
                <option value="name">Recipe Name</option>
                <option value="ingredient">Ingredient</option>
                <option value="cuisine">Cuisine</option>
              </select>
              
              <label htmlFor="searchQuery" className="sr-only">Search Query</label>
              <input
                id="searchQuery"
                name="searchQuery"
                type="text"
                className="search-input"
                placeholder={`Search by ${searchType}...`}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                aria-label="Search for recipes"
              />
              
              <button type="submit" className="btn btn-primary" disabled={loading}>
                <FaSearch />
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>
          </form>

          <AdvancedFilters onApplyFilters={handleApplyFilters} />
        </div>

        <div className="search-results">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

        {loading && (
          <LoadingSkeleton count={8} />
        )}
        {results.length > 0 && (
            <>
              <h2 className="results-title">
                Found {results.length} recipe{results.length !== 1 ? 's' : ''}
              </h2>
              <div className="recipe-grid">
                {results.map((recipe) => (
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

export default Search;
