import React, { useState, useRef, useCallback } from 'react';
import { FaSearch, FaSortAmountDown } from 'react-icons/fa';
import api from '../utils/axios';
import RecipeCard from '../components/RecipeCard';
import LoadingSkeleton from '../components/LoadingSkeleton';
import AdvancedFilters from '../components/AdvancedFilters';
import { useToast } from '../context/ToastContext';
import { useFavorites } from '../context/FavoritesContext';
import './Search.css';

function Search() {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState('name');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { isFavorite, toggleFavorite: ctxToggleFavorite } = useFavorites();
  const [sortBy, setSortBy] = useState('relevance');
  const [filters, setFilters] = useState({
    maxTime: '',
    maxCalories: '',
    maxIngredients: '',
    minIngredients: ''
  });
  const abortRef = useRef(null);
  const lastParamsRef = useRef('');

  const handleSearch = async (e, filterOverride) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!searchQuery.trim()) {
      setError('Please enter a search term');
      return;
    }

    setLoading(true);
    setError('');
    setResults([]);

    // Use passed-in filters if available (avoids stale closure)
    const activeFilters = filterOverride || filters;

    try {
      const params = {
        query: searchQuery,
        type: searchType,
        limit: 50,
        ...(sortBy !== 'relevance' && { sort: sortBy })
      };

      // Add filters if they have positive values (0 or empty = no filter)
      if (activeFilters.maxTime && Number(activeFilters.maxTime) >= 1) params.max_time = Number(activeFilters.maxTime);
      if (activeFilters.maxCalories && Number(activeFilters.maxCalories) >= 1) params.max_calories = Number(activeFilters.maxCalories);
      if (activeFilters.maxIngredients && Number(activeFilters.maxIngredients) >= 1) params.max_ingredients = Number(activeFilters.maxIngredients);
      if (activeFilters.minIngredients && Number(activeFilters.minIngredients) >= 1) params.min_ingredients = Number(activeFilters.minIngredients);

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

      const response = await api.get('/api/search', { params, signal: controller.signal });

      setResults(response.data.results || []);
      
      if (response.data.results.length === 0) {
        setError('No recipes found. Try a different search term.');
      }
    } catch (err) {
      if (err.name === 'CanceledError' || err.code === 'ERR_CANCELED') {
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
    ctxToggleFavorite(recipeId);
  }, [ctxToggleFavorite]);

  const handleApplyFilters = (newFilters) => {
    setFilters(newFilters);
    // If there's an active search, re-run it with the new filters
    // Pass newFilters directly to avoid stale closure reading old state
    if (searchQuery.trim()) {
      handleSearch({ preventDefault: () => {} }, newFilters);
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

          {/* Sort Controls */}
          <div className="sort-controls">
            <FaSortAmountDown />
            <label htmlFor="sortBy" className="sr-only">Sort by</label>
            <select
              id="sortBy"
              className="sort-select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="relevance">Sort: Relevance</option>
              <option value="popular">Most Popular</option>
              <option value="recent">Most Recent</option>
              <option value="rating">Highest Rated</option>
              <option value="name">Name (A-Z)</option>
              <option value="time_asc">Quickest First</option>
            </select>
          </div>
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
                    isFavorite={isFavorite(recipe.id)}
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
