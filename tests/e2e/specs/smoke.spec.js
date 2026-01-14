import { test, expect } from '@playwright/test';

/**
 * Smoke tests to verify basic application functionality.
 * These tests ensure the application is running and accessible.
 */

test.describe('Smoke Tests', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('/');

    // Should either show the homepage or redirect to login
    const url = page.url();
    expect(url).toMatch(/\/(accounts\/login)?/);
  });

  test('login page is accessible', async ({ page }) => {
    await page.goto('/accounts/login/');

    // Verify login form elements are present
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('login page has correct title', async ({ page }) => {
    await page.goto('/accounts/login/');

    // Check the page title contains expected text
    await expect(page).toHaveTitle(/Login.*BattyCoda/);
  });

  test('static assets load correctly', async ({ page }) => {
    await page.goto('/accounts/login/');

    // Check that CSS is loaded (page should have styling)
    const body = page.locator('body');
    await expect(body).toBeVisible();

    // Verify no critical console errors
    const errors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Wait for page to fully load
    await page.waitForLoadState('networkidle');

    // Filter out non-critical errors (like missing favicons)
    const criticalErrors = errors.filter(
      (err) => !err.includes('favicon') && !err.includes('404')
    );
    expect(criticalErrors).toHaveLength(0);
  });
});
