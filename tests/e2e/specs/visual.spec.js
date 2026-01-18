import { test, expect } from '@playwright/test';
import { login } from '../helpers/auth.js';
import { setTheme, applyTheme } from '../helpers/theme.js';
import users from '../fixtures/users.json' with { type: 'json' };

/**
 * Visual regression tests for BattyCoda.
 *
 * These tests capture screenshots of key pages and compare them against baselines.
 * On first run, baselines are created. Subsequent runs compare against baselines.
 *
 * To update baselines after intentional UI changes:
 *   npx playwright test --update-snapshots
 *
 * Each page is tested in both light and dark themes.
 */

// Common screenshot options for consistency
const screenshotOptions = {
  fullPage: true,
  // Allow small differences due to anti-aliasing, font rendering, etc.
  maxDiffPixelRatio: 0.02,
};

// Options for pages with dynamic content (notifications, species links, etc.)
const dynamicPageOptions = {
  ...screenshotOptions,
  // Higher threshold for pages with dynamic content
  maxDiffPixelRatio: 0.05,
};

/**
 * Wait for theme to fully apply (CSS load + repaint)
 */
async function waitForThemeStability(page) {
  // Wait for theme CSS to load and apply
  await page.waitForTimeout(500);

  // Wait for any animations to complete
  await page.evaluate(() => {
    return new Promise((resolve) => {
      requestAnimationFrame(() => {
        requestAnimationFrame(resolve);
      });
    });
  });
}

test.describe('Visual Regression - Login Page', () => {
  test('login page - light theme', async ({ page }) => {
    await setTheme(page, 'light');
    await page.goto('/accounts/login/');
    await page.waitForLoadState('networkidle');

    // Ensure theme is applied
    await applyTheme(page, 'light');
    await waitForThemeStability(page);

    await expect(page).toHaveScreenshot('login-light.png', screenshotOptions);
  });

  test('login page - dark theme', async ({ page }) => {
    await setTheme(page, 'dark');
    await page.goto('/accounts/login/');
    await page.waitForLoadState('networkidle');

    // Ensure theme is applied
    await applyTheme(page, 'dark');
    await waitForThemeStability(page);

    await expect(page).toHaveScreenshot('login-dark.png', screenshotOptions);
  });
});

test.describe('Visual Regression - Registration Page', () => {
  test('registration page - light theme', async ({ page }) => {
    await setTheme(page, 'light');
    await page.goto('/accounts/register/');
    await page.waitForLoadState('networkidle');

    await applyTheme(page, 'light');
    await waitForThemeStability(page);

    await expect(page).toHaveScreenshot('register-light.png', screenshotOptions);
  });

  test('registration page - dark theme', async ({ page }) => {
    await setTheme(page, 'dark');
    await page.goto('/accounts/register/');
    await page.waitForLoadState('networkidle');

    await applyTheme(page, 'dark');
    await waitForThemeStability(page);

    await expect(page).toHaveScreenshot('register-dark.png', screenshotOptions);
  });
});

test.describe('Visual Regression - Authenticated Pages', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, users.testUser.username, users.testUser.password);
  });

  test.describe('Dashboard/Home', () => {
    test('home page - light theme', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      await applyTheme(page, 'light');
      await waitForThemeStability(page);

      // Mask dynamic elements like notifications dropdown
      await expect(page).toHaveScreenshot('home-light.png', {
        ...dynamicPageOptions,
        mask: [page.locator('#notificationsDropdown')],
      });
    });

    test('home page - dark theme', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      await applyTheme(page, 'dark');
      await waitForThemeStability(page);

      await expect(page).toHaveScreenshot('home-dark.png', {
        ...dynamicPageOptions,
        mask: [page.locator('#notificationsDropdown')],
      });
    });
  });

  test.describe('Recordings List', () => {
    test('recordings page - light theme', async ({ page }) => {
      await page.goto('/recordings/');
      await page.waitForLoadState('networkidle');

      await applyTheme(page, 'light');
      await waitForThemeStability(page);

      await expect(page).toHaveScreenshot('recordings-light.png', screenshotOptions);
    });

    test('recordings page - dark theme', async ({ page }) => {
      await page.goto('/recordings/');
      await page.waitForLoadState('networkidle');

      await applyTheme(page, 'dark');
      await waitForThemeStability(page);

      await expect(page).toHaveScreenshot('recordings-dark.png', screenshotOptions);
    });
  });

  test.describe('Projects List', () => {
    test('projects page - light theme', async ({ page }) => {
      await page.goto('/projects/');
      await page.waitForLoadState('networkidle');

      await applyTheme(page, 'light');
      await waitForThemeStability(page);

      await expect(page).toHaveScreenshot('projects-light.png', screenshotOptions);
    });

    test('projects page - dark theme', async ({ page }) => {
      await page.goto('/projects/');
      await page.waitForLoadState('networkidle');

      await applyTheme(page, 'dark');
      await waitForThemeStability(page);

      await expect(page).toHaveScreenshot('projects-dark.png', screenshotOptions);
    });
  });

  test.describe('Clustering Dashboard', () => {
    test('clustering dashboard - light theme', async ({ page }) => {
      await page.goto('/clustering/');
      await page.waitForLoadState('networkidle');

      await applyTheme(page, 'light');
      await waitForThemeStability(page);

      await expect(page).toHaveScreenshot('clustering-dashboard-light.png', screenshotOptions);
    });

    test('clustering dashboard - dark theme', async ({ page }) => {
      await page.goto('/clustering/');
      await page.waitForLoadState('networkidle');

      await applyTheme(page, 'dark');
      await waitForThemeStability(page);

      await expect(page).toHaveScreenshot('clustering-dashboard-dark.png', screenshotOptions);
    });
  });

  test.describe('Create Clustering Run', () => {
    test('create clustering page - light theme', async ({ page }) => {
      await page.goto('/clustering/create/');
      await page.waitForLoadState('networkidle');

      await applyTheme(page, 'light');
      await waitForThemeStability(page);

      await expect(page).toHaveScreenshot('clustering-create-light.png', screenshotOptions);
    });

    test('create clustering page - dark theme', async ({ page }) => {
      await page.goto('/clustering/create/');
      await page.waitForLoadState('networkidle');

      await applyTheme(page, 'dark');
      await waitForThemeStability(page);

      await expect(page).toHaveScreenshot('clustering-create-dark.png', screenshotOptions);
    });
  });
});

test.describe('Visual Regression - Pages Requiring Fixtures', () => {
  // These tests require additional fixtures that may not be set up.
  // They are skipped by default but documented for future implementation.

  test.beforeEach(async ({ page }) => {
    await login(page, users.testUser.username, users.testUser.password);
  });

  // Task Annotation Page
  // Requires: A task batch with at least one task
  test.skip('task annotation page - light theme', async ({ page }) => {
    // Navigate to a specific task
    await page.goto('/task/1/');
    await page.waitForLoadState('networkidle');

    await applyTheme(page, 'light');

    await expect(page).toHaveScreenshot('task-annotation-light.png', screenshotOptions);
  });

  test.skip('task annotation page - dark theme', async ({ page }) => {
    await page.goto('/task/1/');
    await page.waitForLoadState('networkidle');

    await applyTheme(page, 'dark');

    await expect(page).toHaveScreenshot('task-annotation-dark.png', screenshotOptions);
  });

  // Cluster Explorer
  // Requires: A completed clustering run with clusters
  test.skip('cluster explorer - light theme', async ({ page }) => {
    await page.goto('/clustering/explorer/1/');
    await page.waitForLoadState('networkidle');

    // Wait for visualization to render
    await page.waitForSelector('#cluster-visualization svg', { timeout: 10000 });

    await applyTheme(page, 'light');

    await expect(page).toHaveScreenshot('cluster-explorer-light.png', screenshotOptions);
  });

  test.skip('cluster explorer - dark theme', async ({ page }) => {
    await page.goto('/clustering/explorer/1/');
    await page.waitForLoadState('networkidle');

    await page.waitForSelector('#cluster-visualization svg', { timeout: 10000 });

    await applyTheme(page, 'dark');

    await expect(page).toHaveScreenshot('cluster-explorer-dark.png', screenshotOptions);
  });

  // Recording Detail Page
  // Requires: A recording with audio file
  test.skip('recording detail page - light theme', async ({ page }) => {
    await page.goto('/recordings/1/');
    await page.waitForLoadState('networkidle');

    await applyTheme(page, 'light');

    await expect(page).toHaveScreenshot('recording-detail-light.png', screenshotOptions);
  });

  test.skip('recording detail page - dark theme', async ({ page }) => {
    await page.goto('/recordings/1/');
    await page.waitForLoadState('networkidle');

    await applyTheme(page, 'dark');

    await expect(page).toHaveScreenshot('recording-detail-dark.png', screenshotOptions);
  });
});
