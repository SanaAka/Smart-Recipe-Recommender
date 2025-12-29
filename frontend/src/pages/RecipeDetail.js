import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FaClock, FaFire, FaHeart, FaRegHeart, FaArrowLeft, FaUtensils, FaShoppingCart } from 'react-icons/fa';
import axios from 'axios';
import './RecipeDetail.css';

function RecipeDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [recipe, setRecipe] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isFavorite, setIsFavorite] = useState(false);
  const [imageError, setImageError] = useState(false);

  useEffect(() => {
    loadRecipe();
    checkFavoriteStatus();
  }, [id]);

  const loadRecipe = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await axios.get(`/api/recipe/${id}`);
      setRecipe(response.data);
    } catch (err) {
      setError('Failed to load recipe details. Please try again.');
      console.error('Error loading recipe:', err);
    } finally {
      setLoading(false);
    }
  };

  const checkFavoriteStatus = () => {
    const savedFavorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    setIsFavorite(savedFavorites.includes(parseInt(id)));
  };

  const toggleFavorite = () => {
    const savedFavorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    let newFavorites;

    if (savedFavorites.includes(parseInt(id))) {
      newFavorites = savedFavorites.filter(favId => favId !== parseInt(id));
      setIsFavorite(false);
    } else {
      newFavorites = [...savedFavorites, parseInt(id)];
      setIsFavorite(true);
    }

    localStorage.setItem('favorites', JSON.stringify(newFavorites));
  };

  const addToShoppingList = () => {
    if (!recipe || !recipe.ingredients) return;
    
    const shoppingList = JSON.parse(localStorage.getItem('shoppingList') || '[]');
    const newItems = recipe.ingredients.map((ingredient, idx) => ({
      id: `${recipe.id}-${idx}-${Date.now()}`,
      name: ingredient,
      checked: false,
      recipeId: recipe.id,
      recipeName: recipe.name
    }));
    
    const updated = [...shoppingList, ...newItems];
    localStorage.setItem('shoppingList', JSON.stringify(updated));
    
    alert(`Added ${recipe.ingredients.length} ingredients to shopping list!`);
  };

  if (loading) {
    return (
      <div className="recipe-detail-page">
        <div className="container">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (error || !recipe) {
    return (
      <div className="recipe-detail-page">
        <div className="container">
          <div className="error-message">{error}</div>
          <button className="btn btn-primary" onClick={() => navigate('/')}>
            <FaArrowLeft />
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  const imageUrl = recipe.image_url || recipe.image || recipe.imageUrl;

  return (
    <div className="recipe-detail-page">
      <div className="container">
        <button className="back-btn" onClick={() => navigate(-1)}>
          <FaArrowLeft />
          Back
        </button>

        <div className="recipe-detail-card">
          <div className="recipe-header">
            <div className="recipe-hero">
              {imageUrl && !imageError ? (
                <img 
                  src={imageUrl}
                  alt={recipe.name}
                  className="hero-image"
                  onError={() => setImageError(true)}
                />
              ) : (
                <FaUtensils className="hero-icon" />
              )}
            </div>
            
            <div className="recipe-title-section">
              <h1 className="recipe-name">{recipe.name}</h1>
              
              <div className="recipe-meta-bar">
                {recipe.minutes && (
                  <div className="meta-badge">
                    <FaClock />
                    <span>{recipe.minutes} minutes</span>
                  </div>
                )}
                {recipe.calories && (
                  <div className="meta-badge">
                    <FaFire />
                    <span>{Math.round(recipe.calories)} calories</span>
                  </div>
                )}
                
                <button 
                  className={`favorite-toggle ${isFavorite ? 'favorited' : ''}`}
                  onClick={toggleFavorite}
                >
                  {isFavorite ? <FaHeart /> : <FaRegHeart />}
                  <span>{isFavorite ? 'Saved' : 'Save'}</span>
                </button>
                
                <button 
                  className="shopping-cart-btn"
                  onClick={addToShoppingList}
                >
                  <FaShoppingCart />
                  <span>Add to List</span>
                </button>
              </div>
            </div>
          </div>

          {recipe.tags && recipe.tags.length > 0 && (
            <div className="recipe-section">
              <h2 className="section-title">Tags</h2>
              <div className="tags-list">
                {recipe.tags.map((tag, index) => (
                  <span key={index} className="tag">{tag}</span>
                ))}
              </div>
            </div>
          )}

          {recipe.ingredients && recipe.ingredients.length > 0 && (
            <div className="recipe-section">
              <h2 className="section-title">Ingredients</h2>
              <ul className="ingredients-list">
                {recipe.ingredients.map((ingredient, index) => (
                  <li key={index}>{ingredient}</li>
                ))}
              </ul>
            </div>
          )}

          {recipe.steps && recipe.steps.length > 0 && (
            <div className="recipe-section">
              <h2 className="section-title">Instructions</h2>
              <ol className="steps-list">
                {recipe.steps.map((step, index) => (
                  <li key={index}>{step}</li>
                ))}
              </ol>
            </div>
          )}

          {recipe.description && (
            <div className="recipe-section">
              <h2 className="section-title">Description</h2>
              <p className="description-text">{recipe.description}</p>
            </div>
          )}

          {recipe.nutrition && (
            <div className="recipe-section">
              <h2 className="section-title">Nutrition Information</h2>
              {Object.values(recipe.nutrition).some(val => parseFloat(val) > 0) ? (
                <div className="nutrition-grid">
                  {Object.entries(recipe.nutrition)
                    .filter(([key, value]) => parseFloat(value) > 0)
                    .map(([key, value]) => (
                      <div key={key} className="nutrition-item">
                        <span className="nutrition-label">{key}</span>
                        <span className="nutrition-value">{value}</span>
                      </div>
                    ))}
                </div>
              ) : (
                <p className="description-text" style={{fontStyle: 'italic', color: '#718096'}}>
                  Nutrition information not available for this recipe.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default RecipeDetail;
