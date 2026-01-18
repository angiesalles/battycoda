/**
 * Theme helpers for Playwright E2E tests.
 * Provides utilities for switching between light and dark themes.
 */

/**
 * Set the theme via localStorage before page load.
 * Call this BEFORE navigating to a page.
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {'light' | 'dark'} theme - Theme name
 */
export async function setTheme(page, theme) {
  // Set theme in localStorage before navigating
  await page.addInitScript((themeName) => {
    localStorage.setItem('battycoda_theme', themeName);
  }, theme);
}

/**
 * Apply theme after page is loaded.
 * Use this when the page is already loaded.
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {'light' | 'dark'} theme - Theme name
 */
export async function applyTheme(page, theme) {
  await page.evaluate((themeName) => {
    // Set localStorage
    localStorage.setItem('battycoda_theme', themeName);

    // Apply theme class to body
    const mainBody = document.getElementById('main-body');
    if (mainBody) {
      mainBody.className = mainBody.className.replace(/theme-[a-z-]+/g, '').trim();
      mainBody.classList.add(`theme-${themeName}`);
    }

    // Use global applyTheme if available
    if (typeof window.applyTheme === 'function') {
      window.applyTheme(themeName);
    }
  }, theme);

  // Wait for theme CSS to load
  await page.waitForTimeout(300);
}

/**
 * Get the current theme from the page.
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @returns {Promise<string>} Current theme name
 */
export async function getCurrentTheme(page) {
  return page.evaluate(() => {
    const mainBody = document.getElementById('main-body');
    if (mainBody) {
      const themeClass = mainBody.className.match(/theme-([a-z-]+)/);
      return themeClass ? themeClass[1] : 'light';
    }
    return localStorage.getItem('battycoda_theme') || 'light';
  });
}
