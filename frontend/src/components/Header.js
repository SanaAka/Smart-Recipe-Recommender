import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FaUtensils, FaSearch, FaHeart, FaHome, FaBars, FaTimes, FaShoppingCart } from 'react-icons/fa';
import './Header.css';

function Header() {
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  const toggleMenu = () => {
    setMenuOpen(!menuOpen);
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
        </nav>
      </div>
    </header>
  );
}

export default Header;
