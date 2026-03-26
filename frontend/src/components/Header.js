import React, { useState, useContext } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { FaUtensils, FaSearch, FaHeart, FaHome, FaBars, FaTimes, FaShoppingCart, FaUser, FaSignOutAlt, FaSignInAlt, FaPlusCircle, FaShieldAlt, FaCog } from 'react-icons/fa';
import { AuthContext } from '../App';
import ThemeToggle from './ThemeToggle';
import UserAvatar from './UserAvatar';
import './Header.css';

function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const { isAuthenticated, user, logout } = useContext(AuthContext);

  const toggleMenu = () => {
    setMenuOpen(!menuOpen);
  };

  const handleLogout = () => {
    logout();
    setMenuOpen(false);
    navigate('/');
  };

  return (
    <header className="header">
      <div className="header-content">
        <Link to="/" className="logo">
          <FaUtensils className="logo-icon" />
          <span>Smart Recipe Recommender</span>
        </Link>
        
        <button className="menu-toggle" onClick={toggleMenu}>
          {menuOpen ? <FaTimes /> : <FaBars />}
        </button>

        <nav className={`nav ${menuOpen ? 'nav-open' : ''}`}>
          <Link 
            to="/" 
            className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
            onClick={() => setMenuOpen(false)}
          >
            <FaHome />
            <span>Home</span>
          </Link>
          <Link 
            to="/search" 
            className={`nav-link ${location.pathname === '/search' ? 'active' : ''}`}
            onClick={() => setMenuOpen(false)}
          >
            <FaSearch />
            <span>Search</span>
          </Link>
          <Link 
            to="/favorites" 
            className={`nav-link ${location.pathname === '/favorites' ? 'active' : ''}`}
            onClick={() => setMenuOpen(false)}
          >
            <FaHeart />
            <span>Favorites</span>
          </Link>
          <Link 
            to="/shopping-list" 
            className={`nav-link ${location.pathname === '/shopping-list' ? 'active' : ''}`}
            onClick={() => setMenuOpen(false)}
          >
            <FaShoppingCart />
            <span>Shopping</span>
          </Link>

          {isAuthenticated && (
            <Link 
              to="/create-recipe" 
              className={`nav-link ${location.pathname === '/create-recipe' ? 'active' : ''}`}
              onClick={() => setMenuOpen(false)}
            >
              <FaPlusCircle />
              <span>Post Recipe</span>
            </Link>
          )}

          {isAuthenticated && user?.role === 'admin' && (
            <Link 
              to="/admin" 
              className={`nav-link admin-link ${location.pathname === '/admin' ? 'active' : ''}`}
              onClick={() => setMenuOpen(false)}
            >
              <FaShieldAlt />
              <span>Admin</span>
            </Link>
          )}

          <div className="nav-divider"></div>

          <ThemeToggle />

          {isAuthenticated ? (
            <>
              <Link to={`/user/${user?.username}`} className="user-info" onClick={() => setMenuOpen(false)}>
                <UserAvatar username={user?.username} profilePic={user?.profile_pic} size="sm" />
                <span className="username">{user?.username}</span>
              </Link>
              <Link
                to="/settings"
                className={`nav-link settings-link ${location.pathname === '/settings' ? 'active' : ''}`}
                onClick={() => setMenuOpen(false)}
              >
                <FaCog />
                <span>Settings</span>
              </Link>
              <button 
                className="nav-link logout-btn" 
                onClick={handleLogout}
              >
                <FaSignOutAlt />
                <span>Logout</span>
              </button>
            </>
          ) : (
            <Link 
              to="/login" 
              className={`nav-link login-btn ${location.pathname === '/login' ? 'active' : ''}`}
              onClick={() => setMenuOpen(false)}
            >
              <FaSignInAlt />
              <span>Login</span>
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Header;
