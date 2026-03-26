import React, { Suspense, lazy, useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import Header from './components/Header';
import ErrorBoundary from './components/ErrorBoundary';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './context/ToastContext';
import { ConfirmProvider } from './context/ConfirmContext';
import { FavoritesProvider } from './context/FavoritesContext';
import './App.css';
import './theme.css';

// Scroll to top on route change
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
}

const Home = lazy(() => import('./pages/Home'));
const Search = lazy(() => import('./pages/Search'));
const Favorites = lazy(() => import('./pages/Favorites'));
const RecipeDetail = lazy(() => import('./pages/RecipeDetail'));
const ShoppingList = lazy(() => import('./pages/ShoppingList'));
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const CreateRecipe = lazy(() => import('./pages/CreateRecipe'));
const UserProfile = lazy(() => import('./pages/UserProfile'));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));
const AccountSettings = lazy(() => import('./pages/AccountSettings'));
const EditRecipe = lazy(() => import('./pages/EditRecipe'));
const NotFound = lazy(() => import('./pages/NotFound'));

// Auth Context
export const AuthContext = React.createContext({
  isAuthenticated: false,
  user: null,
  login: () => {},
  logout: () => {},
  token: null
});

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  useEffect(() => {
    // Check for existing auth on mount and validate the token
    const savedToken = localStorage.getItem('authToken');
    const savedUser = localStorage.getItem('user');
    
    if (savedToken && savedUser) {
      // Quick client-side expiry check for JWT tokens
      try {
        const payload = JSON.parse(atob(savedToken.split('.')[1]));
        if (payload.exp && payload.exp * 1000 < Date.now()) {
          // Token expired — clear stale auth
          localStorage.removeItem('authToken');
          localStorage.removeItem('user');
          return;
        }
      } catch {
        // Malformed token — clear it
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        return;
      }
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
      setIsAuthenticated(true);
    }
  }, []);

  const login = (authToken, userData) => {
    localStorage.setItem('authToken', authToken);
    localStorage.setItem('user', JSON.stringify(userData));
    setToken(authToken);
    setUser(userData);
    setIsAuthenticated(true);
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
  };

  const authContextValue = {
    isAuthenticated,
    user,
    token,
    login,
    logout
  };

  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ToastProvider>
        <ConfirmProvider>
        <AuthContext.Provider value={authContextValue}>
        <FavoritesProvider isAuthenticated={isAuthenticated} token={token}>
          <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            <ScrollToTop />
            <div className="App">
              <Header />
              <main className="main-content">
                <Suspense fallback={
                  <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <p>Loading...</p>
                  </div>
                }>
                  <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/search" element={<Search />} />
                    <Route path="/favorites" element={<Favorites />} />
                    <Route path="/shopping-list" element={<ShoppingList />} />
                    <Route path="/recipe/:id" element={<RecipeDetail />} />
                    <Route path="/create-recipe" element={<CreateRecipe />} />
                    <Route path="/user/:username" element={<UserProfile />} />
                    <Route path="/admin" element={<AdminDashboard />} />
                    <Route path="/settings" element={<AccountSettings />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                    <Route path="/edit-recipe/:id" element={<EditRecipe />} />
                    <Route path="*" element={<NotFound />} />
                  </Routes>
                </Suspense>
              </main>
              <footer className="app-footer">
                <div className="footer-content">
                  <p>© 2026 Smart Recipe Recommender v3.0</p>
                  <p className="footer-subtitle">Made with ❤️ by SanaAka</p>
                </div>
              </footer>
            </div>
          </Router>
        </FavoritesProvider>
        </AuthContext.Provider>
        </ConfirmProvider>
        </ToastProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
