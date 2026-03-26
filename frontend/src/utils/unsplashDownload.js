/**
 * Trigger an Unsplash download event.
 * Required by Unsplash API guidelines when a user selects/uses an image.
 * See: https://help.unsplash.com/en/articles/2511258-guideline-triggering-a-download
 *
 * @param {string} downloadLocation - The download_location URL from Unsplash API
 */
import api from './axios';

export async function triggerUnsplashDownload(downloadLocation) {
  if (!downloadLocation || !downloadLocation.includes('unsplash.com')) return;

  try {
    await api.post('/api/images/track-download', {
      download_location: downloadLocation
    });
  } catch (err) {
    // Silent fail — download tracking is non-critical
    console.warn('Unsplash download tracking failed:', err.message);
  }
}

export default triggerUnsplashDownload;
