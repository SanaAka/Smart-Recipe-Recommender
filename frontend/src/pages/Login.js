import React, { useState, useContext } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FaUser, FaLock, FaSignInAlt } from 'react-icons/fa';
import api from '../utils/axios';
import { AuthContext } from '../App';
import { useToast } from '../context/ToastContext';
import './Auth.css';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);
  const { toast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await api.post('/api/auth/login', {
        username,
        password
      });

      // Save auth data
      login(response.data.access_token, response.data.user);
      toast.success(`Welcome back, ${response.data.user.username}!`);

      // Redirect to home
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Please check your credentials.');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <div className="auth-icon">
              <FaSignInAlt />
            </div>
            <h1>Welcome Back!</h1>
            <p>Sign in to access your personalized recipes</p>
          </div>

          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-group">
              <label htmlFor="username">
                <FaUser className="input-icon" />
                Username
              </label>
              <input
                id="username"
                type="text"
                className="input"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">
                <FaLock className="input-icon" />
                Password
              </label>
              <input
                id="password"
                type="password"
                className="input"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <button 
              type="submit" 
              className="btn btn-primary btn-full"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="btn-spinner"></span>
                  Signing in...
                </>
              ) : (
                <>
                  <FaSignInAlt />
                  Sign In
                </>
              )}
            </button>
          </form>

          <div className="auth-footer">
            <p>
              Don't have an account?{' '}
              <Link to="/register" className="auth-link">
                Create one now
              </Link>
            </p>
          </div>

          <div className="demo-credentials">
            <p className="demo-title">Demo Account:</p>
            <p className="demo-text">
              <strong>Username:</strong> john_doe<br/>
              <strong>Password:</strong> SecurePass123!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;
