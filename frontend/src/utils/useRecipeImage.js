import { useState, useEffect, useRef } from 'react';
import api from './axios';
import { getCategoryFallback } from './categoryImages';

// ── Caches ──────────────────────────────────────────────────────────────
const imageCache = {};          // recipeId → url string
const photoInfoCache = {};      // recipeId → { photographer, photographer_url, unsplash_url, download_location }
const pendingIds = new Set();   // ids waiting to be batched
let batchTimer = null;          // debounce timer for batching
const batchResolvers = {};      // recipeId → [{ resolve }]

// ── Config ──────────────────────────────────────────────────────────────
const BATCH_DELAY = 150;        // ms to wait before firing batch request
const BATCH_MAX   = 40;         // max ids per batch call

/**
 * Check if a URL is a dead source.unsplash.com link.
 */
function isBrokenUrl(url) {
  if (!url) return true;
  return url.includes('source.unsplash.com');
}

/**
 * Schedule a batch fetch — collects IDs over BATCH_DELAY ms,
 * then sends one POST /api/images/batch instead of N individual GETs.
 */
function requestBatchImage(recipeId) {
  return new Promise((resolve) => {
    // Already cached?
    if (imageCache[recipeId] !== undefined) {
      resolve(imageCache[recipeId]);
      return;
    }

    // Register resolver
    if (!batchResolvers[recipeId]) {
      batchResolvers[recipeId] = [];
    }
    batchResolvers[recipeId].push({ resolve });
    pendingIds.add(recipeId);

    // Debounce: wait a short time to collect more IDs
    if (batchTimer) clearTimeout(batchTimer);
    batchTimer = setTimeout(flushBatch, BATCH_DELAY);

    // Also flush if we've hit the cap
    if (pendingIds.size >= BATCH_MAX) {
      clearTimeout(batchTimer);
      flushBatch();
    }
  });
}

/**
 * Actually fire the batch request for all pending IDs.
 */
async function flushBatch() {
  batchTimer = null;
  if (pendingIds.size === 0) return;

  const ids = [...pendingIds];
  pendingIds.clear();

  try {
    const resp = await api.post('/api/images/batch', { ids });
    const images = resp.data?.images || {};

    for (const id of ids) {
      const imgData = images[String(id)] || {};
      const url = imgData.url || null;
      imageCache[id] = url;

      // Cache photographer attribution info
      if (imgData.photographer) {
        photoInfoCache[id] = {
          photographer: imgData.photographer,
          photographer_url: imgData.photographer_url || '',
          unsplash_url: imgData.unsplash_url || '',
          download_location: imgData.download_location || ''
        };
      }

      // Resolve all waiting callers for this id
      if (batchResolvers[id]) {
        batchResolvers[id].forEach((r) => r.resolve(url));
        delete batchResolvers[id];
      }
    }
  } catch {
    // On failure, resolve everyone with null so they show placeholder
    for (const id of ids) {
      imageCache[id] = null;
      if (batchResolvers[id]) {
        batchResolvers[id].forEach((r) => r.resolve(null));
        delete batchResolvers[id];
      }
    }
  }
}

/**
 * Hook that returns a working image URL for a recipe.
 *
 * - Uses batch API to fetch many images in one request
 * - Deduplicates concurrent calls for the same recipe
 * - Lazy: only fetches when the component is in the viewport
 *
 * @param {number} recipeId
 * @param {string} originalUrl
 * @param {{ lazy?: boolean, recipeName?: string }} options
 * @returns {{ imageUrl: string|null, loading: boolean, containerRef: React.RefObject, photoInfo: object|null }}
 */
export function useRecipeImage(recipeId, originalUrl, options = {}) {
  const { lazy = true, recipeName = '' } = options;

  const [imageUrl, setImageUrl] = useState(() => {
    // Good URL (e.g. user-uploaded) always takes priority
    if (!isBrokenUrl(originalUrl)) return originalUrl;
    if (imageCache[recipeId] !== undefined) return imageCache[recipeId];
    // Instant category-based fallback — no API call, no waiting
    return getCategoryFallback(recipeName);
  });
  const [loading, setLoading] = useState(false);  // Never show loading — fallback is instant
  const [photoInfo, setPhotoInfo] = useState(() => photoInfoCache[recipeId] || null);

  const containerRef = useRef(null);
  const cancelledRef = useRef(false);
  const fetchedRef   = useRef(false);

  useEffect(() => {
    cancelledRef.current = false;
    fetchedRef.current   = false;

    if (!recipeId) return;

    // Good URL from API (e.g. user-uploaded image) — always takes priority
    if (!isBrokenUrl(originalUrl)) {
      imageCache[recipeId] = originalUrl;
      setImageUrl(originalUrl);
      setLoading(false);
      return;
    }

    // Already cached (only used when originalUrl is broken/missing)
    if (imageCache[recipeId] !== undefined) {
      setImageUrl(imageCache[recipeId]);
      setPhotoInfo(photoInfoCache[recipeId] || null);
      setLoading(false);
      return;
    }

    // Show instant category fallback while real image loads in background
    const fallback = getCategoryFallback(recipeName);
    setImageUrl(fallback);
    setLoading(false);

    // Helper: fetch real image in background (silently upgrades the fallback)
    const doFetch = () => {
      if (fetchedRef.current || cancelledRef.current) return;
      fetchedRef.current = true;
      requestBatchImage(recipeId).then((url) => {
        if (!cancelledRef.current && url) {
          setImageUrl(url);  // Upgrade from fallback to real image
          // Also update photoInfo if available
          if (photoInfoCache[recipeId]) {
            setPhotoInfo(photoInfoCache[recipeId]);
          }
        }
      });
    };

    // Lazy mode: wait until the element is in the viewport
    if (lazy && typeof IntersectionObserver !== 'undefined' && containerRef.current) {
      const observer = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting) {
            doFetch();
            observer.disconnect();
          }
        },
        { rootMargin: '200px' }  // prefetch 200px before visible
      );
      observer.observe(containerRef.current);
      return () => {
        cancelledRef.current = true;
        observer.disconnect();
      };
    }

    // Non-lazy or no IntersectionObserver
    doFetch();
    return () => {
      cancelledRef.current = true;
    };
  }, [recipeId, originalUrl, lazy]);

  return { imageUrl, loading, containerRef, photoInfo };
}
