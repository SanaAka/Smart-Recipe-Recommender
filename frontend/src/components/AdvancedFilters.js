import React, { useState } from 'react';
import { FaFilter, FaTimes } from 'react-icons/fa';
import './AdvancedFilters.css';

function AdvancedFilters({ onApplyFilters }) {
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    maxTime: '',
    maxCalories: '',
    maxIngredients: '',
    minIngredients: ''
  });

  const handleApply = () => {
    onApplyFilters(filters);
    setShowFilters(false);
  };

  const handleReset = () => {
    const resetFilters = {
      maxTime: '',
      maxCalories: '',
      maxIngredients: '',
      minIngredients: ''
    };
    setFilters(resetFilters);
    onApplyFilters(resetFilters);
  };

  return (
    <div className="advanced-filters">
      <button 
        className="filter-toggle-btn"
        onClick={() => setShowFilters(!showFilters)}
      >
        <FaFilter />
        {showFilters ? 'Hide Filters' : 'Show Filters'}
      </button>

      {showFilters && (
        <div className="filters-panel">
          <div className="filters-grid">
            <div className="filter-item">
              <label htmlFor="maxTime">Max Cooking Time (minutes)</label>
              <input
                id="maxTime"
                name="maxTime"
                type="number"
                min="1"
                placeholder="e.g., 30"
                value={filters.maxTime}
                onChange={(e) => setFilters({...filters, maxTime: e.target.value})}
                aria-label="Maximum cooking time in minutes"
              />
            </div>

            <div className="filter-item">
              <label htmlFor="maxCalories">Max Calories</label>
              <input
                id="maxCalories"
                name="maxCalories"
                type="number"
                min="1"
                placeholder="e.g., 500"
                value={filters.maxCalories}
                onChange={(e) => setFilters({...filters, maxCalories: e.target.value})}
                aria-label="Maximum calories"
              />
            </div>

            <div className="filter-item">
              <label htmlFor="minIngredients">Min Ingredients</label>
              <input
                id="minIngredients"
                name="minIngredients"
                type="number"
                min="1"
                placeholder="e.g., 3"
                value={filters.minIngredients}
                onChange={(e) => setFilters({...filters, minIngredients: e.target.value})}
                aria-label="Minimum number of ingredients"
              />
            </div>

            <div className="filter-item">
              <label htmlFor="maxIngredients">Max Ingredients</label>
              <input
                id="maxIngredients"
                name="maxIngredients"
                type="number"
                min="1"
                placeholder="e.g., 10"
                value={filters.maxIngredients}
                onChange={(e) => setFilters({...filters, maxIngredients: e.target.value})}
                aria-label="Maximum number of ingredients"
              />
            </div>
          </div>

          <div className="filter-actions">
            <button className="btn btn-secondary" onClick={handleReset}>
              <FaTimes />
              Reset
            </button>
            <button className="btn btn-primary" onClick={handleApply}>
              <FaFilter />
              Apply Filters
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdvancedFilters;
