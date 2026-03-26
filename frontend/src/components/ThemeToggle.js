import React from 'react';
import { FaMoon, FaSun } from 'react-icons/fa';
import { useTheme } from '../context/ThemeContext';
import './ThemeToggle.css';

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button 
      className="theme-toggle" 
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
      title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      <div className="theme-toggle-icon">
        {theme === 'light' ? (
          <FaMoon className="icon moon-icon" />
        ) : (
          <FaSun className="icon sun-icon" />
        )}
      </div>
      <span className="theme-label">
        {theme === 'light' ? 'Dark' : 'Light'}
      </span>
    </button>
  );
}

export default ThemeToggle;
