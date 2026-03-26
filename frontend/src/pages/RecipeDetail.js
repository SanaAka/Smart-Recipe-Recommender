import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { FaClock, FaFire, FaHeart, FaRegHeart, FaArrowLeft, FaUtensils, FaShoppingCart, FaUser, FaWineGlassAlt, FaSignal, FaEdit } from 'react-icons/fa';
import api from '../utils/axios';
import { useRecipeImage } from '../utils/useRecipeImage';
import StarRating from '../components/StarRating';
import Comments from '../components/Comments';
import { AuthContext } from '../App';
import { useToast } from '../context/ToastContext';
import { useFavorites } from '../context/FavoritesContext';
import './RecipeDetail.css';

function RecipeDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const { toast } = useToast();
  const { isFavorite: checkFav, toggleFavorite: ctxToggle } = useFavorites();
  const [recipe, setRecipe] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [imageError, setImageError] = useState(false);
  const [rating, setRating] = useState({ avg_rating: 0, rating_count: 0, user_rating: null });
  const [winePairings, setWinePairings] = useState([]);
  const [difficulty, setDifficulty] = useState(null);

  // Must call hooks before any early returns
  const rawImageUrl = recipe ? (recipe.image_url || recipe.image || recipe.imageUrl) : null;
  const { imageUrl, loading: imgLoading, containerRef: heroRef, photoInfo } = useRecipeImage(recipe?.id || id, rawImageUrl, { lazy: false, recipeName: recipe?.name || '' });
  const [imgLoaded, setImgLoaded] = useState(false);

  useEffect(() => {
    loadRecipe();
    loadRating();
    loadDifficulty();
    loadWinePairings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const loadRating = async () => {
    try {
      const response = await api.get(`/api/recipe/${id}/rating`);
      setRating(response.data);
    } catch (err) {
      console.error('Failed to load rating:', err);
    }
  };

  const handleRate = async (stars) => {
    if (!user) {
      toast.warning('Please login to rate recipes');
      navigate('/login');
      return;
    }

    try {
      const response = await api.post(`/api/recipe/${id}/rating`, { rating: stars });
      setRating({
        avg_rating: response.data.avg_rating,
        rating_count: response.data.rating_count,
        user_rating: stars
      });
      toast.success(`Rated ${stars} star${stars > 1 ? 's' : ''}!`);
    } catch (err) {
      console.error('Failed to rate recipe:', err);
      toast.error(err.response?.data?.error || 'Failed to submit rating');
    }
  };

  const handleRemoveRating = async () => {
    try {
      const response = await api.delete(`/api/recipe/${id}/rating`);
      setRating({
        avg_rating: response.data.avg_rating,
        rating_count: response.data.rating_count,
        user_rating: null
      });
      toast.info('Rating removed');
    } catch (err) {
      console.error('Failed to remove rating:', err);
      toast.error(err.response?.data?.error || 'Failed to remove rating');
    }
  };

  const loadRecipe = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await api.get(`/api/recipe/${id}`);
      setRecipe(response.data);
    } catch (err) {
      setError('Failed to load recipe details. Please try again.');
      console.error('Error loading recipe:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadDifficulty = async () => {
    try {
      const response = await api.get(`/api/recipe/${id}/difficulty`);
      setDifficulty(response.data.difficulty);
    } catch (err) {
      // Silently fail - difficulty is optional
    }
  };

  const loadWinePairings = async () => {
    try {
      const response = await api.get(`/api/recipe/${id}/wine-pairings`);
      setWinePairings(response.data.pairings || []);
    } catch (err) {
      // Silently fail - wine pairings are optional
    }
  };

  const isFavorite = checkFav(id);

  const toggleFavorite = () => {
    ctxToggle(parseInt(id));
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
    
    toast.success(`Added ${recipe.ingredients.length} ingredients to shopping list!`);
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

  // imageUrl is already resolved by the hook above

  return (
    <div className="recipe-detail-page">
      <div className="container">
        <button className="back-btn" onClick={() => navigate(-1)}>
          <FaArrowLeft />
          Back
        </button>

        <div className="recipe-detail-card">
          <div className="recipe-header">
            <div className="recipe-hero" ref={heroRef}>
              {(imgLoading || (imageUrl && !imgLoaded && !imageError)) && (
                <div className="image-shimmer" />
              )}
              {imageUrl && !imageError ? (
                <img 
                  src={imageUrl}
                  alt={recipe.name}
                  className={`hero-image ${imgLoaded ? 'loaded' : 'loading'}`}
                  onLoad={() => setImgLoaded(true)}
                  onError={() => setImageError(true)}
                />
              ) : !imgLoading ? (
                <FaUtensils className="hero-icon" />
              ) : null}
            </div>
            
            {/* Unsplash attribution (required by API guidelines) */}
            {photoInfo && photoInfo.photographer && (
              <div className="unsplash-attribution-detail">
                Photo by{' '}
                <a href={photoInfo.photographer_url} target="_blank" rel="noopener noreferrer">
                  {photoInfo.photographer}
                </a>
                {' '}on{' '}
                <a href={photoInfo.unsplash_url} target="_blank" rel="noopener noreferrer">
                  Unsplash
                </a>
              </div>
            )}
            
            <div className="recipe-title-section">
              <h1 className="recipe-name">{recipe.name}</h1>
              
              {recipe.submitted_by_username && (
                <div className="recipe-author">
                  <FaUser />
                  <span>Posted by </span>
                  <Link to={`/user/${recipe.submitted_by_username}`} className="author-link">
                    {recipe.submitted_by_username}
                  </Link>
                </div>
              )}

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
                {difficulty && (
                  <div className={`meta-badge difficulty-${difficulty.difficulty_level}`}>
                    <FaSignal />
                    <span>{difficulty.difficulty_level}</span>
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

                {user && recipe.submitted_by_username === user.username && (
                  <button 
                    className="edit-recipe-btn"
                    onClick={() => navigate(`/edit-recipe/${recipe.id}`)}
                  >
                    <FaEdit />
                    <span>Edit</span>
                  </button>
                )}
              </div>
              
              {/* Rating Section */}
              <div className="rating-section">
                <StarRating
                  value={rating.user_rating || rating.avg_rating}
                  count={rating.rating_count}
                  userRating={rating.user_rating}
                  onRate={handleRate}
                  onRemove={handleRemoveRating}
                  readOnly={!user}
                  size="large"
                />
                {!user && rating.user_rating === null && (
                  <p className="rating-hint">Login to rate this recipe</p>
                )}
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
          
          {/* Wine Pairings Section */}
          {winePairings.length > 0 && (
            <div className="recipe-section wine-pairings-section">
              <h2 className="section-title"><FaWineGlassAlt /> Wine Pairings</h2>
              <div className="wine-grid">
                {winePairings.map((pairing, index) => (
                  <div key={index} className={`wine-card wine-${pairing.wine_type?.toLowerCase()}`}>
                    <span className="wine-icon">{pairing.wine_type === 'Red' ? '🍷' : '🥂'}</span>
                    <span className="wine-name">{pairing.wine_name}</span>
                    <span className="wine-type">{pairing.wine_type}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Comments Section */}
          <Comments recipeId={id} />
        </div>
      </div>
    </div>
  );
}

export default RecipeDetail;
