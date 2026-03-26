import React, { useState, useContext } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FaUser, FaLock, FaEnvelope, FaUserPlus } from 'react-icons/fa';
import api from '../utils/axios';
import { AuthContext } from '../App';
import { useToast } from '../context/ToastContext';
import './Auth.css';

function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);
  const { toast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validation
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    setLoading(true);

    try {
      const response = await api.post('/api/auth/register', {
        username,
        email,
        password
      });

      // Auto-login after registration
      login(response.data.access_token, response.data.user);
      toast.success('Account created! Welcome aboard!');

      // Redirect to home
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed. Please try again.');
      console.error('Registration error:', err);
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
              <FaUserPlus />
            </div>
            <h1>Join Us Today!</h1>
            <p>Create your account and start discovering amazing recipes</p>
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
                placeholder="Choose a username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
                minLength={3}
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">
                <FaEnvelope className="input-icon" />
                Email Address
              </label>
              <input
                id="email"
                type="email"
                className="input"
                placeholder="your.email@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
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
                placeholder="Create a strong password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
              <small className="form-hint">
                Min 8 characters, with uppercase, lowercase, and a number
              </small>
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">
                <FaLock className="input-icon" />
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                className="input"
                placeholder="Re-enter your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
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
                  Creating Account...
                </>
              ) : (
                <>
                  <FaUserPlus />
                  Create Account
                </>
              )}
            </button>
          </form>

          <div className="auth-footer">
            <p>
              Already have an account?{' '}
              <Link to="/login" className="auth-link">
                Sign in here
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Register;
