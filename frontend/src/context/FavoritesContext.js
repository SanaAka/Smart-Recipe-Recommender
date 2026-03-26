import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import api from '../utils/axios';
import { useToast } from './ToastContext';

const FavoritesContext = createContext({
  favorites: [],
  isFavorite: () => false,
  toggleFavorite: () => {},
  removeFavorite: () => {},
  clearAllFavorites: () => {},
  loading: false,
});

export function FavoritesProvider({ children, isAuthenticated, token }) {
  const { toast } = useToast();
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(false);
  const syncedRef = useRef(false);
  const prevAuthRef = useRef(false);

  // ── Load favorites on mount / auth change ──────────────────────────
  useEffect(() => {
    if (isAuthenticated && token) {
      // User just logged in – fetch from backend and merge any localStorage ones
      const localFavs = JSON.parse(localStorage.getItem('favorites') || '[]');

      const fetchAndSync = async () => {
        setLoading(true);
        try {
          if (localFavs.length > 0 && !syncedRef.current) {
            // Merge localStorage favorites into backend
            const res = await api.post('/api/favorites/sync', { recipe_ids: localFavs });
            setFavorites(res.data.favorite_ids || []);
            // Clear localStorage now that they're in the backend
            localStorage.removeItem('favorites');
            syncedRef.current = true;
          } else {
            // Just fetch from backend
            const res = await api.get('/api/favorites/ids');
            setFavorites(res.data.favorite_ids || []);
          }
        } catch (err) {
          console.error('Failed to load favorites from backend:', err);
          // Fallback to localStorage if backend fails
          setFavorites(localFavs);
        } finally {
          setLoading(false);
        }
      };

      fetchAndSync();
    } else {
      // Not authenticated – use localStorage
      const localFavs = JSON.parse(localStorage.getItem('favorites') || '[]');
      setFavorites(localFavs);
      syncedRef.current = false;
    }

    prevAuthRef.current = isAuthenticated;
  }, [isAuthenticated, token]);

  // ── Check if a recipe is a favorite ────────────────────────────────
  const isFavorite = useCallback(
    (recipeId) => favorites.includes(Number(recipeId)),
    [favorites]
  );

  // ── Toggle favorite ────────────────────────────────────────────────
  const toggleFavorite = useCallback(
    async (recipeId) => {
      const rid = Number(recipeId);
      const wasFavorite = favorites.includes(rid);

      // Optimistic UI update
      const newFavorites = wasFavorite
        ? favorites.filter((id) => id !== rid)
        : [...favorites, rid];
      setFavorites(newFavorites);

      if (isAuthenticated) {
        try {
          if (wasFavorite) {
            await api.delete(`/api/favorites/${rid}`);
            toast.info('Removed from favorites');
          } else {
            await api.post(`/api/favorites/${rid}`);
            toast.success('Added to favorites ❤️');
          }
        } catch (err) {
          // Revert on failure
          setFavorites(favorites);
          toast.error('Failed to update favorites');
          console.error('Favorite toggle error:', err);
        }
      } else {
        // Not authenticated – persist to localStorage
        localStorage.setItem('favorites', JSON.stringify(newFavorites));
        if (wasFavorite) {
          toast.info('Removed from favorites');
        } else {
          toast.success('Added to favorites ❤️');
        }
      }
    },
    [favorites, isAuthenticated, toast]
  );

  // ── Remove without toast (for Favorites page bulk actions) ─────────
  const removeFavorite = useCallback(
    async (recipeId) => {
      const rid = Number(recipeId);
      const newFavorites = favorites.filter((id) => id !== rid);
      setFavorites(newFavorites);

      if (isAuthenticated) {
        try {
          await api.delete(`/api/favorites/${rid}`);
        } catch (err) {
          setFavorites(favorites);
          console.error('Remove favorite error:', err);
        }
      } else {
        localStorage.setItem('favorites', JSON.stringify(newFavorites));
      }
      toast.info('Removed from favorites');
    },
    [favorites, isAuthenticated, toast]
  );

  // ── Clear all favorites ────────────────────────────────────────────
  const clearAllFavorites = useCallback(async () => {
    const prevFavorites = [...favorites];
    setFavorites([]);

    if (isAuthenticated) {
      try {
        // Remove each one from backend
        await Promise.all(prevFavorites.map((rid) => api.delete(`/api/favorites/${rid}`)));
      } catch (err) {
        setFavorites(prevFavorites);
        toast.error('Failed to clear favorites');
        console.error('Clear favorites error:', err);
        return;
      }
    } else {
      localStorage.setItem('favorites', JSON.stringify([]));
    }
    toast.success('All favorites cleared');
  }, [favorites, isAuthenticated, toast]);

  const value = {
    favorites,
    isFavorite,
    toggleFavorite,
    removeFavorite,
    clearAllFavorites,
    loading,
  };

  return (
    <FavoritesContext.Provider value={value}>
      {children}
    </FavoritesContext.Provider>
  );
}

export function useFavorites() {
  return useContext(FavoritesContext);
}

export default FavoritesContext;
