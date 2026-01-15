import { test, expect } from '@playwright/test';
import { login } from '../helpers/auth.js';
import users from '../fixtures/users.json' with { type: 'json' };

/**
 * End-to-end tests for recording workflows.
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

test.describe('Recordings - Authenticated', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, users.testUser.username, users.testUser.password);
  });

  test('displays recordings list page', async ({ page }) => {
    await page.goto('/recordings/');

    // Should show the recordings page with title (h5 is used in list_view_base.html)
    await expect(page.locator('h5.card-title')).toContainText('All Recordings');
  });

  test('shows empty state or recordings table', async ({ page }) => {
    await page.goto('/recordings/');

    // Either shows recordings table or empty state message
    const recordingsTable = page.locator('table:has(th:has-text("Name"))');
    const emptyMessage = page.locator('.text-center:has-text("No")');

    // One of these should be visible
    const hasRecordings = await recordingsTable.isVisible();
    const hasEmptyMessage = await emptyMessage.isVisible();

    expect(hasRecordings || hasEmptyMessage).toBe(true);
  });

  test('has new recording button', async ({ page }) => {
    await page.goto('/recordings/');

    // Should have a link to create a new recording (use first() as there may be multiple)
    await expect(page.locator('a:has-text("New Recording")').first()).toBeVisible();
  });

  test('has batch upload button', async ({ page }) => {
    await page.goto('/recordings/');

    // Should have a batch upload button
    await expect(page.locator('a:has-text("Batch Upload")')).toBeVisible();
  });

  test('has project filter dropdown', async ({ page }) => {
    await page.goto('/recordings/');

    // Should have a project filter dropdown
    await expect(page.locator('#project-filter')).toBeVisible();
  });

  test('new recording button navigates to create page', async ({ page }) => {
    await page.goto('/recordings/');

    await page.click('a:has-text("New Recording")');

    // Should navigate to create recording page
    await expect(page).toHaveURL(/\/recordings\/create/);
  });

  test('batch upload button navigates to batch upload page', async ({
    page,
  }) => {
    await page.goto('/recordings/');

    await page.click('a:has-text("Batch Upload")');

    // Should navigate to batch upload page
    await expect(page).toHaveURL(/\/recordings\/batch-upload/);
  });
});

test.describe('Create Recording - Authenticated', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, users.testUser.username, users.testUser.password);
  });

  test('create recording page loads', async ({ page }) => {
    await page.goto('/recordings/create/');

    // Should show create form with header
    await expect(page.locator('h5:has-text("Create New Recording")')).toBeVisible();
  });

  test('create recording form has required fields', async ({ page }) => {
    await page.goto('/recordings/create/');

    // Should have file upload field
    await expect(page.locator('input[type="file"]')).toBeVisible();

    // Should have submit button
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });
});

test.describe('Batch Upload - Authenticated', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, users.testUser.username, users.testUser.password);
  });

  test('batch upload page loads', async ({ page }) => {
    await page.goto('/recordings/batch-upload/');

    // Should show batch upload page with header
    await expect(page.locator('h5:has-text("Simple Batch Upload")')).toBeVisible();
  });

  test('batch upload form has file input', async ({ page }) => {
    await page.goto('/recordings/batch-upload/');

    // Should have file upload field (use first() as there may be multiple)
    await expect(page.locator('input[type="file"]').first()).toBeVisible();
  });
})
