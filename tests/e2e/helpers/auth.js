/**
 * Authentication helpers for Playwright E2E tests.
 * Provides utilities for logging in, logging out, and managing test users.
 */

/**
 * Log in a user via the login form.
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} username - Username or email address
 * @param {string} password - User password
 * @returns {Promise<void>}
 */
export async function login(page, username, password) {
  await page.goto('/accounts/login/');
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');

  // Wait for navigation after login
  await page.waitForURL((url) => !url.pathname.includes('/accounts/login'));
}

/**
 * Log out the current user.
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @returns {Promise<void>}
 */
export async function logout(page) {
  await page.goto('/accounts/logout/');
  // Wait for redirect to login page or home
  await page.waitForLoadState('networkidle');
}

/**
 * Check if a user is currently logged in.
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @returns {Promise<boolean>}
 */
export async function isLoggedIn(page) {
  // Check for presence of logout link or user menu
  const logoutLink = page.locator('a[href*="logout"]');
  return (await logoutLink.count()) > 0;
}

/**
 * Navigate to a page that requires authentication, handling login redirect if needed.
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} url - Target URL
 * @param {Object} credentials - Login credentials
 * @param {string} credentials.username - Username or email
 * @param {string} credentials.password - Password
 * @returns {Promise<void>}
 */
export async function navigateWithAuth(page, url, credentials) {
  await page.goto(url);

  // Check if we were redirected to login
  if (page.url().includes('/accounts/login')) {
    await login(page, credentials.username, credentials.password);
    // Navigate to the original URL after login
    await page.goto(url);
  }
}
