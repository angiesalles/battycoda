import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for BattyCoda E2E testing.
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/e2e/specs',

  // Global setup and teardown for test data
  globalSetup: './tests/e2e/global-setup.js',
  globalTeardown: './tests/e2e/global-teardown.js',

  // Run tests in parallel
  fullyParallel: true,

  // Fail fast on CI
  forbidOnly: !!process.env.CI,

  // Retry failed tests
  retries: process.env.CI ? 2 : 0,

  // Limit parallel workers on CI to avoid resource issues
  workers: process.env.CI ? 1 : undefined,

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
  ],

  // Shared settings for all projects
  use: {
    // Base URL for Django test server (port 8088 to avoid conflicts with production on 8000)
    baseURL: process.env.BASE_URL || `http://localhost:${process.env.TEST_PORT || 8088}`,

    // Collect trace on failure
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video on failure
    video: 'on-first-retry',
  },

  // Configure projects for browser testing (Chromium only)
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Start Django dev server before tests with test database (port 8088 to avoid conflicts)
  webServer: {
    command: `bash -c "source venv/bin/activate && DJANGO_TEST_MODE=true python manage.py runserver ${process.env.TEST_PORT || 8088}"`,
    url: `http://localhost:${process.env.TEST_PORT || 8088}`,
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
    env: {
      DJANGO_TEST_MODE: 'true',
    },
  },

  // Output directory for test artifacts
  outputDir: 'test-results',
});
