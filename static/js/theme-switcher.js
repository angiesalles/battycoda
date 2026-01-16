/**
 * Theme Switcher Module
 *
 * Allows users to switch between different Maisonnette themes.
 * Works for both authenticated and non-authenticated users.
 */

import { getCsrfToken } from './utils/page-data.js';

const LOCAL_STORAGE_THEME_KEY = 'battycoda_theme';

/**
 * Save theme to localStorage (works for all users as fallback)
 * @param {string} themeName - Theme name to save
 */
function saveThemeToLocalStorage(themeName) {
  try {
    localStorage.setItem(LOCAL_STORAGE_THEME_KEY, themeName);
  } catch {
    // localStorage might be unavailable (private browsing, storage quota, etc.)
    // Silently ignore - theme will still work for current session
  }
}

/**
 * Update theme preference on server for authenticated users
 * @param {string} themeName - Theme name to save
 */
function updateThemePreference(themeName) {
  fetch('/update_theme_preference/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify({ theme: themeName }),
  })
    .then((response) => {
      if (!response.ok) {
        // Server save failed - localStorage fallback is already saved
        console.warn('Failed to save theme to server, using localStorage fallback');
      }
    })
    .catch((error) => {
      // Network error - localStorage fallback is already saved
      console.warn('Error saving theme to server, using localStorage fallback:', error);
    });
}

/**
 * Get the URL for a theme CSS file.
 * Uses Vite manifest URLs if available (set by vite_theme_urls template tag),
 * otherwise falls back to static URL.
 * @param {string} themeName - Theme name
 * @returns {string} URL for the theme CSS file
 */
function getThemeUrl(themeName) {
  // Check for Vite-provided theme URLs
  if (window.__VITE_THEME_URLS__ && window.__VITE_THEME_URLS__[themeName]) {
    return window.__VITE_THEME_URLS__[themeName];
  }
  // Fallback to static URL
  return `/static/css/themes/${themeName}.css`;
}

/**
 * Apply a theme by adding/removing CSS classes and loading theme CSS
 * @param {string} themeName - Theme name to apply
 */
export function applyTheme(themeName) {
  const mainBody = document.getElementById('main-body');
  if (!mainBody) return;

  // Remove all theme classes from body
  mainBody.className = mainBody.className.replace(/theme-[a-z-]+/g, '').trim();

  // Add new theme class to body
  mainBody.classList.add(`theme-${themeName}`);

  // Only load theme CSS if it's not the default theme
  if (themeName !== 'default') {
    const themeId = `theme-css-${themeName}`;
    let themeLink = document.getElementById(themeId);

    if (!themeLink) {
      themeLink = document.createElement('link');
      themeLink.id = themeId;
      themeLink.rel = 'stylesheet';
      themeLink.href = getThemeUrl(themeName);
      document.head.appendChild(themeLink);
    }
  }

  // If switching to default, remove all theme CSS files
  if (themeName === 'default') {
    document.querySelectorAll('link[id^="theme-css-"]').forEach((link) => {
      link.parentNode.removeChild(link);
    });
  }
}

/**
 * Initialize the theme switcher
 */
export function initialize() {
  const mainBody = document.getElementById('main-body');
  const themeSwitcherLinks = document.querySelectorAll('.theme-switcher-link');

  if (!mainBody) return;

  // Check if user is authenticated
  const isAuthenticated = document.getElementById('logoutLink') !== null;

  // If not authenticated, apply theme from localStorage
  if (!isAuthenticated) {
    const savedTheme = localStorage.getItem(LOCAL_STORAGE_THEME_KEY);
    if (savedTheme) {
      applyTheme(savedTheme);

      // Update active state in dropdown
      themeSwitcherLinks.forEach((link) => {
        if (link.dataset.theme === savedTheme) {
          link.classList.add('active');
        }
      });
    }
  }

  // Add click event to each theme switcher link
  themeSwitcherLinks.forEach((link) => {
    link.addEventListener('click', function (e) {
      e.preventDefault();

      const themeName = this.dataset.theme;

      // Always save to localStorage first (immediate persistence/fallback)
      saveThemeToLocalStorage(themeName);

      // For authenticated users, also sync to server (for cross-device sync)
      if (isAuthenticated) {
        updateThemePreference(themeName);
      }

      applyTheme(themeName);

      // Update active state in dropdown
      themeSwitcherLinks.forEach((l) => l.classList.remove('active'));
      this.classList.add('active');
    });
  });
}

// Auto-initialize on DOMContentLoaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
}

// Expose globally for potential external use
window.applyTheme = applyTheme;

// Export for testing
export { saveThemeToLocalStorage };
