import React, { useState, useEffect, useContext, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { FaUser, FaUtensils, FaCommentDots, FaStar, FaCalendarAlt, FaArrowLeft, FaClock, FaCamera, FaTrash, FaFlag } from 'react-icons/fa';
import api from '../utils/axios';
import { AuthContext } from '../App';
import { useToast } from '../context/ToastContext';
import { useConfirm } from '../context/ConfirmContext';
import UserAvatar from '../components/UserAvatar';
import ReportModal from '../components/ReportModal';
import './UserProfile.css';

function UserProfile() {
  const { username } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { confirm } = useConfirm();
  const { user: authUser, login: authLogin, token } = useContext(AuthContext);
  const fileInputRef = useRef(null);
  const [profile, setProfile] = useState(null);
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);

  const isOwnProfile = authUser?.username === username;

  useEffect(() => {
    loadProfile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [username]);

  const loadProfile = async () => {
    setLoading(true);
    setError('');
    try {
      const [profileRes, recipesRes] = await Promise.all([
        api.get(`/api/user/${username}/profile`),
        api.get(`/api/user/${username}/recipes`)
      ]);
      setProfile(profileRes.data);
      setRecipes(recipesRes.data.recipes || []);
    } catch (err) {
      if (err.response?.status === 404) {
        setError('User not found');
      } else {
        setError('Failed to load profile');
      }
      toast.error(err.response?.data?.error || 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteRecipe = async (recipeId, recipeName) => {
    const ok = await confirm({
      title: 'Delete Recipe',
      message: `Are you sure you want to delete "${recipeName}"? This cannot be undone.`,
      confirmText: 'Delete',
      danger: true
    });
    if (!ok) return;
    try {
      await api.delete(`/api/recipes/${recipeId}/delete`);
      setRecipes(prev => prev.filter(r => r.id !== recipeId));
      setProfile(prev => prev ? { ...prev, recipe_count: Math.max(0, (prev.recipe_count || 1) - 1) } : prev);
      toast.success('Recipe deleted!');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to delete recipe');
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Unknown';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  };

  if (loading) {
    return (
      <div className="user-profile-page">
        <div className="container">
          <div className="spinner"></div>
          <p className="loading-text">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="user-profile-page">
        <div className="container">
          <div className="profile-error">
            <FaUser className="error-icon" />
            <h2>{error}</h2>
            <p>The user you're looking for doesn't exist or the profile couldn't be loaded.</p>
            <button className="btn btn-primary" onClick={() => navigate(-1)}>
              <FaArrowLeft /> Go Back
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="user-profile-page">
      <div className="container">
        <button className="back-btn" onClick={() => navigate(-1)}>
          <FaArrowLeft /> Back
        </button>

        {/* Profile Header */}
        <div className="profile-header-card">
          <div className="profile-avatar-wrap">
            <UserAvatar username={username} profilePic={profile?.profile_pic} size="xl" />
            {isOwnProfile && (
              <>
                <button
                  className="avatar-upload-btn"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  title="Change profile picture"
                >
                  <FaCamera />
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
                  style={{ display: 'none' }}
                  onChange={async (e) => {
                    const file = e.target.files?.[0];
                    if (!file) return;
                    setUploading(true);
                    try {
                      const fd = new FormData();
                      fd.append('image', file);
                      const res = await api.put('/api/user/profile-pic', fd, {
                        headers: { 'Content-Type': 'multipart/form-data' }
                      });
                      const newPic = res.data.profile_pic;
                      setProfile(prev => ({ ...prev, profile_pic: newPic }));
                      // Update AuthContext so Header avatar refreshes
                      if (authUser) {
                        authLogin(token, { ...authUser, profile_pic: newPic });
                      }
                      toast.success('Profile picture updated!');
                    } catch (err) {
                      toast.error(err.response?.data?.error || 'Upload failed');
                    } finally {
                      setUploading(false);
                      e.target.value = '';
                    }
                  }}
                />
              </>
            )}
          </div>
          <div className="profile-info">
            <h1 className="profile-username">{username}</h1>
            {profile?.bio && (
              <p className="profile-bio">{profile.bio}</p>
            )}
            <div className="profile-joined">
              <FaCalendarAlt />
              <span>Member since {formatDate(profile?.member_since)}</span>
            </div>
            {/* Report button - visible for other users' profiles */}
            {authUser && !isOwnProfile && (
              <button className="btn-report-user" onClick={() => setShowReportModal(true)}>
                <FaFlag /> Report User
              </button>
            )}
          </div>
        </div>

        {/* Stats Grid */}
        <div className="profile-stats">
          <div className="stat-card">
            <FaUtensils className="stat-icon recipes-icon" />
            <div className="stat-value">{profile?.recipe_count || 0}</div>
            <div className="stat-label">Recipes</div>
          </div>
          <div className="stat-card">
            <FaCommentDots className="stat-icon comments-icon" />
            <div className="stat-value">{profile?.comment_count || 0}</div>
            <div className="stat-label">Comments</div>
          </div>
          <div className="stat-card">
            <FaStar className="stat-icon rating-icon" />
            <div className="stat-value">
              {profile?.avg_rating_received > 0
                ? `${profile.avg_rating_received} ★`
                : '—'}
            </div>
            <div className="stat-label">Avg Rating</div>
          </div>
        </div>

        {/* Recipes Section */}
        <div className="profile-recipes-section">
          <h2 className="section-title">
            <FaUtensils /> Recipes by {username}
          </h2>

          {recipes.length === 0 ? (
            <div className="no-recipes">
              <p>This user hasn't posted any recipes yet.</p>
            </div>
          ) : (
            <div className="profile-recipes-grid">
              {recipes.map(recipe => (
                <div key={recipe.id} className="profile-recipe-card-wrap">
                  <Link
                    to={`/recipe/${recipe.id}`}
                    className="profile-recipe-card"
                  >
                    <div className="profile-recipe-image">
                      {recipe.image_url ? (
                        <img
                          src={recipe.image_url.startsWith('/') ? `${api.defaults.baseURL?.replace('/api', '') || ''}${recipe.image_url}` : recipe.image_url}
                          alt={recipe.name}
                          onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
                        />
                      ) : null}
                      <div className="recipe-img-placeholder" style={recipe.image_url ? { display: 'none' } : {}}>
                        <FaUtensils />
                      </div>
                    </div>
                    <div className="profile-recipe-info">
                      <h3>{recipe.name}</h3>
                      {recipe.description && (
                        <p className="recipe-desc">{recipe.description.slice(0, 100)}{recipe.description.length > 100 ? '...' : ''}</p>
                      )}
                      <div className="recipe-meta">
                        {recipe.minutes > 0 && (
                          <span className="meta-item"><FaClock /> {recipe.minutes} min</span>
                        )}
                        {recipe.avg_rating > 0 && (
                          <span className="meta-item"><FaStar /> {recipe.avg_rating} ({recipe.rating_count})</span>
                        )}
                      </div>
                    </div>
                  </Link>
                  {isOwnProfile && (
                    <button
                      className="recipe-delete-btn"
                      onClick={() => handleDeleteRecipe(recipe.id, recipe.name)}
                      title="Delete recipe"
                    >
                      <FaTrash />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Report Modal */}
        {showReportModal && (
          <ReportModal
            username={username}
            onClose={() => setShowReportModal(false)}
          />
        )}
      </div>
    </div>
  );
}

export default UserProfile;
