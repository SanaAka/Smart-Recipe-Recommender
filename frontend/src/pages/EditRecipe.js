import React, { useState, useContext, useRef, useEffect } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { AuthContext } from '../App';
import { useToast } from '../context/ToastContext';
import { FaUpload, FaLink, FaTimesCircle, FaImage } from 'react-icons/fa';
import api from '../utils/axios';
import './CreateRecipe.css'; // reuse same styles

const EditRecipe = () => {
  const { id } = useParams();
  const { user } = useContext(AuthContext);
  const { toast } = useToast();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [minutes, setMinutes] = useState('');
  const [nSteps, setNSteps] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [imageMode, setImageMode] = useState('url');
  const [uploading, setUploading] = useState(false);
  const [uploadedPreview, setUploadedPreview] = useState(null);
  const fileInputRef = useRef(null);
  const [ingredients, setIngredients] = useState(['']);
  const [steps, setSteps] = useState(['']);
  const [tags, setTags] = useState([]);
  const [tagInput, setTagInput] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRecipe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const loadRecipe = async () => {
    try {
      const response = await api.get(`/api/recipe/${id}`);
      const r = response.data;
      setName(r.name || '');
      setDescription(r.description || '');
      setMinutes(r.minutes ? String(r.minutes) : '');
      setNSteps(r.n_steps ? String(r.n_steps) : '');
      setImageUrl(r.image_url || '');
      setIngredients(r.ingredients && r.ingredients.length > 0 ? r.ingredients : ['']);
      setSteps(r.steps && r.steps.length > 0 ? r.steps : ['']);
      setTags(r.tags || []);
      if (r.image_url) setImageMode('url');
    } catch (err) {
      setError('Failed to load recipe for editing.');
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="create-recipe-page">
        <div className="login-required">
          <h2>🔒 Login Required</h2>
          <p>You need to be logged in to edit a recipe.</p>
          <Link to="/login">Go to Login</Link>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="create-recipe-page">
        <div className="loading-container"><div className="loading-spinner"></div><p>Loading recipe...</p></div>
      </div>
    );
  }

  // ─── Ingredients ───
  const addIngredient = () => setIngredients([...ingredients, '']);
  const removeIngredient = (i) => {
    if (ingredients.length <= 1) return;
    setIngredients(ingredients.filter((_, idx) => idx !== i));
  };
  const updateIngredient = (i, val) => {
    const copy = [...ingredients]; copy[i] = val; setIngredients(copy);
  };

  // ─── Steps ───
  const addStep = () => setSteps([...steps, '']);
  const removeStep = (i) => {
    if (steps.length <= 1) return;
    setSteps(steps.filter((_, idx) => idx !== i));
  };
  const updateStep = (i, val) => {
    const copy = [...steps]; copy[i] = val; setSteps(copy);
  };

  // ─── Tags ───
  const handleTagKeyDown = (e) => {
    if ((e.key === 'Enter' || e.key === ',') && tagInput.trim()) {
      e.preventDefault();
      const newTag = tagInput.trim().toLowerCase();
      if (!tags.includes(newTag) && tags.length < 15) setTags([...tags, newTag]);
      setTagInput('');
    } else if (e.key === 'Backspace' && !tagInput && tags.length > 0) {
      setTags(tags.slice(0, -1));
    }
  };
  const removeTag = (i) => setTags(tags.filter((_, idx) => idx !== i));

  // ─── Image Upload ───
  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const allowed = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
    if (!allowed.includes(file.type)) { setError('Invalid file type.'); return; }
    if (file.size > 5 * 1024 * 1024) { setError('Image too large. Max 5 MB.'); return; }
    const localPreview = URL.createObjectURL(file);
    setUploadedPreview(localPreview);
    setError('');
    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('image', file);
      const res = await api.post('/api/upload/image', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      setImageUrl(res.data.image_url);
      toast.success('Image uploaded!');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload image');
      setUploadedPreview(null); setImageUrl('');
    } finally { setUploading(false); }
  };

  const clearImage = () => {
    setImageUrl(''); setUploadedPreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // ─── Submit (PUT) ───
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!name.trim()) { setError('Recipe name is required'); return; }
    const validIngredients = ingredients.filter(i => i.trim());
    if (validIngredients.length === 0) { setError('At least one ingredient is required'); return; }
    const validSteps = steps.filter(s => s.trim());
    if (validSteps.length === 0) { setError('At least one step is required'); return; }

    try {
      setSubmitting(true);
      const payload = {
        name: name.trim(),
        description: description.trim() || null,
        minutes: minutes ? parseInt(minutes, 10) : null,
        n_steps: nSteps ? parseInt(nSteps, 10) : validSteps.length,
        ingredients: validIngredients,
        steps: validSteps,
        tags: tags.length > 0 ? tags : [],
        image_url: imageUrl.trim() || null,
      };

      await api.put(`/api/recipes/${id}/edit`, payload);
      toast.success('Recipe updated successfully! ✅');
      navigate(`/recipe/${id}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update recipe. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="create-recipe-page">
      <h1>✏️ Edit Recipe</h1>
      <p className="subtitle">Update your recipe details</p>

      <form className="recipe-form" onSubmit={handleSubmit}>
        {error && <div className="form-error">{error}</div>}

        <div className="form-group">
          <label>Recipe Name <span className="required">*</span></label>
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Grandma's Chicken Soup" maxLength={200} />
        </div>

        <div className="form-group">
          <label>Description</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="A brief description..." maxLength={2000} rows={3} />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Prep Time (minutes)</label>
            <input type="number" value={minutes} onChange={(e) => setMinutes(e.target.value)} placeholder="e.g. 45" min={0} />
          </div>
          <div className="form-group">
            <label>Number of Steps</label>
            <input type="number" value={nSteps} onChange={(e) => setNSteps(e.target.value)} placeholder="Auto-detected" min={1} />
            <span className="form-hint">Leave blank to auto-count from steps below</span>
          </div>
        </div>

        {/* Recipe Image */}
        <div className="form-group">
          <label>Recipe Image</label>
          <div className="image-mode-toggle">
            <button type="button" className={`mode-btn ${imageMode === 'upload' ? 'active' : ''}`} onClick={() => { setImageMode('upload'); if (imageMode !== 'upload') clearImage(); }}>
              <FaUpload /> Upload Photo
            </button>
            <button type="button" className={`mode-btn ${imageMode === 'url' ? 'active' : ''}`} onClick={() => { setImageMode('url'); if (imageMode !== 'url') clearImage(); }}>
              <FaLink /> Paste URL
            </button>
          </div>
          {imageMode === 'upload' ? (
            <div className="image-upload-area">
              {!uploadedPreview && !imageUrl ? (
                <label className="upload-dropzone" htmlFor="edit-recipe-image-input">
                  <FaImage className="dropzone-icon" />
                  <span className="dropzone-text">Click to choose an image</span>
                  <span className="dropzone-hint">PNG, JPG, GIF, WEBP — max 5 MB</span>
                  <input id="edit-recipe-image-input" ref={fileInputRef} type="file" accept="image/png,image/jpeg,image/gif,image/webp" onChange={handleImageUpload} style={{ display: 'none' }} />
                </label>
              ) : (
                <div className="image-preview uploaded">
                  {uploading && <div className="upload-spinner">Uploading...</div>}
                  <img src={uploadedPreview || imageUrl} alt="Preview" onError={(e) => { e.target.style.display = 'none'; }} onLoad={(e) => { e.target.style.display = 'block'; }} />
                  <button type="button" className="clear-image-btn" onClick={clearImage}><FaTimesCircle /> Remove</button>
                </div>
              )}
            </div>
          ) : (
            <>
              <input type="url" value={imageUrl} onChange={(e) => { setImageUrl(e.target.value); setUploadedPreview(null); }} placeholder="https://example.com/my-recipe.jpg" />
              <span className="form-hint">Direct link to an image of your dish</span>
              {imageUrl && (
                <div className="image-preview">
                  <img src={imageUrl} alt="Preview" onError={(e) => { e.target.style.display = 'none'; }} onLoad={(e) => { e.target.style.display = 'block'; }} />
                </div>
              )}
            </>
          )}
        </div>

        {/* Ingredients */}
        <div className="form-group">
          <label>Ingredients <span className="required">*</span></label>
          <div className="dynamic-list">
            {ingredients.map((ing, i) => (
              <div key={i} className="dynamic-list-item">
                <input type="text" value={ing} onChange={(e) => updateIngredient(i, e.target.value)} placeholder={`Ingredient ${i + 1}`} />
                {ingredients.length > 1 && (
                  <button type="button" className="remove-item-btn" onClick={() => removeIngredient(i)}>×</button>
                )}
              </div>
            ))}
            <button type="button" className="add-item-btn" onClick={addIngredient}>+ Add Ingredient</button>
          </div>
        </div>

        {/* Steps */}
        <div className="form-group">
          <label>Steps <span className="required">*</span></label>
          <div className="dynamic-list">
            {steps.map((step, i) => (
              <div key={i} className="dynamic-list-item">
                <span className="step-number">{i + 1}</span>
                <textarea value={step} onChange={(e) => updateStep(i, e.target.value)} placeholder={`Step ${i + 1}...`} rows={2} />
                {steps.length > 1 && (
                  <button type="button" className="remove-item-btn" onClick={() => removeStep(i)}>×</button>
                )}
              </div>
            ))}
            <button type="button" className="add-item-btn" onClick={addStep}>+ Add Step</button>
          </div>
        </div>

        {/* Tags */}
        <div className="form-group">
          <label>Tags</label>
          <div className="tags-input-group" onClick={() => document.getElementById('edit-tag-input').focus()}>
            {tags.map((tag, i) => (
              <span key={i} className="tag-chip">
                {tag}
                <button type="button" onClick={() => removeTag(i)}>×</button>
              </span>
            ))}
            <input id="edit-tag-input" type="text" value={tagInput} onChange={(e) => setTagInput(e.target.value)} onKeyDown={handleTagKeyDown} placeholder={tags.length === 0 ? 'Type a tag and press Enter...' : ''} />
          </div>
          <span className="form-hint">Press Enter or comma to add a tag (max 15)</span>
        </div>

        {/* Submit */}
        <div className="form-submit">
          <button type="submit" className="primary-btn" disabled={submitting}>
            {submitting ? 'Saving...' : '✅ Save Changes'}
          </button>
          <button type="button" className="secondary-btn" onClick={() => navigate(`/recipe/${id}`)}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default EditRecipe;
