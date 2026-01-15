import { test, expect } from '@playwright/test';

/**
 * End-to-end tests for recording workflows.
 *
 * NOTE: Tests requiring authentication are currently skipped due to
 * E2E test infrastructure issues with login. See battycoda-jwt bead.
 *
 * The login works in auth.spec.js tests but fails in this file with
 * identical code. Investigation needed.
 */

test.describe('Recordings - Unauthenticated', () => {
  test('recordings page redirects to login when not authenticated', async ({
    page,
  }) => {
    await page.goto('/recordings/');

    // Should redirect to login
    await expect(page).toHaveURL(/\/accounts\/login/);

    // Should show login form
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
  });

  test('create recording page redirects to login when not authenticated', async ({
    page,
  }) => {
    await page.goto('/recordings/create/');

    // Should redirect to login
    await expect(page).toHaveURL(/\/accounts\/login/);
  });

  test('batch upload page redirects to login when not authenticated', async ({
    page,
  }) => {
    await page.goto('/recordings/batch-upload/');

    // Should redirect to login
    await expect(page).toHaveURL(/\/accounts\/login/);
  });
});

// TODO: Add authenticated tests once E2E login issue is resolved
// See auth.spec.js "after login, redirects to originally requested page" for working pattern
