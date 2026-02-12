import { test, expect } from '@playwright/test';
import { login } from '../helpers/auth.js';
import users from '../fixtures/users.json' with { type: 'json' };

/**
 * End-to-end tests for the clustering workflow.
 *
 * NOTE: Some tests require additional fixtures that are not yet set up:
 * - Segmented recordings with segments
 * - Completed clustering runs
 *
 * Tests that require these fixtures are marked with test.skip() and describe
 * what fixtures are needed. See battycoda-hxh bead for fixture creation work.
 */

test.describe('Clustering - Unauthenticated', () => {
  test('clustering dashboard redirects to login when not authenticated', async ({
    page,
  }) => {
    await page.goto('/clustering/');

    // Should redirect to login
    await expect(page).toHaveURL(/\/accounts\/login/);

    // Should show login form
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
  });

  test('create clustering run page redirects to login when not authenticated', async ({
    page,
  }) => {
    await page.goto('/clustering/create/');

    // Should redirect to login
    await expect(page).toHaveURL(/\/accounts\/login/);
  });

  test('cluster explorer redirects to login when not authenticated', async ({
    page,
  }) => {
    // Try to access explorer for a run (ID 1 may not exist, but should redirect regardless)
    await page.goto('/clustering/explorer/1/');

    // Should redirect to login
    await expect(page).toHaveURL(/\/accounts\/login/);
  });

  test('cluster mapping redirects to login when not authenticated', async ({
    page,
  }) => {
    // Try to access mapping for a run
    await page.goto('/clustering/mapping/1/');

    // Should redirect to login
    await expect(page).toHaveURL(/\/accounts\/login/);
  });
});

test.describe('Clustering Dashboard - Authenticated', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, users.testUser.username, users.testUser.password);
  });

  test('displays clustering dashboard', async ({ page }) => {
    await page.goto('/clustering/');

    // Should show the dashboard with title (use first() since there are multiple card-titles)
    await expect(page.locator('h3.card-title').first()).toContainText(
      'Clustering Dashboard'
    );

    // Should have the "Create New Clustering Run" button
    await expect(
      page.locator('a:has-text("Create New Clustering Run")')
    ).toBeVisible();
  });

  test('displays available clustering algorithms', async ({ page }) => {
    await page.goto('/clustering/');

    // Should show algorithms section
    await expect(
      page.locator('h3.card-title:has-text("Available Clustering Algorithms")')
    ).toBeVisible();

    // At least one algorithm should be displayed (from initialize_defaults command)
    const algorithmCards = page.locator('.card:has-text("K-Means")');
    // May or may not have algorithms depending on test data setup
  });

  test('shows empty state message when no clustering runs exist', async ({
    page,
  }) => {
    await page.goto('/clustering/');

    // Either shows runs table or empty state message
    const runsTable = page.locator('table:has(th:has-text("Name"))');
    const emptyMessage = page.locator('.alert-info:has-text("No clustering runs yet")');

    // One of these should be visible
    const hasRuns = await runsTable.isVisible();
    const hasEmptyMessage = await emptyMessage.isVisible();

    expect(hasRuns || hasEmptyMessage).toBe(true);
  });

  test('create new clustering run link navigates to create page', async ({
    page,
  }) => {
    await page.goto('/clustering/');

    await page.click('a:has-text("Create New Clustering Run")');

    await expect(page).toHaveURL(/\/clustering\/create/);
  });
});

test.describe('Create Clustering Run - Authenticated', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, users.testUser.username, users.testUser.password);
  });

  test('form displays all required fields', async ({ page }) => {
    await page.goto('/clustering/create/');

    // Basic Information section
    await expect(page.locator('#name')).toBeVisible();
    await expect(page.locator('#description')).toBeVisible();

    // Data Selection section - scope radio buttons
    await expect(page.locator('#scope_segmentation')).toBeVisible();
    await expect(page.locator('#scope_project')).toBeVisible();

    // Segmentation dropdown (visible by default)
    await expect(page.locator('#segmentation')).toBeVisible();

    // Algorithm dropdown
    await expect(page.locator('#algorithm')).toBeVisible();

    // Feature extraction dropdown
    await expect(page.locator('#feature_method')).toBeVisible();

    // Submit button
    await expect(
      page.locator('button[type="submit"]:has-text("Create Clustering Run")')
    ).toBeVisible();
  });

  test('scope toggle switches between segmentation and project modes', async ({
    page,
  }) => {
    await page.goto('/clustering/create/');

    // Initially segmentation mode - segmentation dropdown visible, project hidden
    await expect(page.locator('#segmentation_group')).toBeVisible();
    await expect(page.locator('#project_group')).toBeHidden();

    // Switch to project scope
    await page.click('label[for="scope_project"]');

    // Wait for animation
    await page.waitForTimeout(400);

    // Now project dropdown should be visible, segmentation hidden
    await expect(page.locator('#segmentation_group')).toBeHidden();
    await expect(page.locator('#project_group')).toBeVisible();

    // Switch back to segmentation
    await page.click('label[for="scope_segmentation"]');

    // Wait for animation
    await page.waitForTimeout(400);

    // Back to original state
    await expect(page.locator('#segmentation_group')).toBeVisible();
    await expect(page.locator('#project_group')).toBeHidden();
  });

  test('algorithm selection shows/hides number of clusters field', async ({
    page,
  }) => {
    await page.goto('/clustering/create/');

    // Number of clusters field should be hidden initially
    await expect(page.locator('#n_clusters_group')).toBeHidden();

    // Select a manual algorithm (K-Means should show cluster count)
    const algorithm = page.locator('#algorithm');
    const kmeansOption = algorithm.locator('option:has-text("K-Means")');

    // Only test if K-Means option exists (depends on test data)
    if ((await kmeansOption.count()) > 0) {
      await algorithm.selectOption({ label: /K-Means/ });

      // Wait for animation
      await page.waitForTimeout(400);

      // Number of clusters should now be visible
      await expect(page.locator('#n_clusters_group')).toBeVisible();
    }
  });

  test('feature extraction method dropdown has expected options', async ({
    page,
  }) => {
    await page.goto('/clustering/create/');

    const featureMethod = page.locator('#feature_method');

    // Check that dropdown exists and has expected options
    // Check that dropdown exists and has expected options
    await expect(featureMethod).toBeVisible();
    await expect(featureMethod.locator('option[value="mfcc"]')).toHaveCount(1);
    await expect(
      featureMethod.locator('option[value="mel_spectrogram"]')
    ).toHaveCount(1);
    await expect(featureMethod.locator('option[value="chroma"]')).toHaveCount(1);
  });

  test('back to dashboard link works', async ({ page }) => {
    await page.goto('/clustering/create/');

    await page.click('a:has-text("Back to Dashboard")');

    await expect(page).toHaveURL(/\/clustering\/$/);
  });

  test('cancel button returns to dashboard', async ({ page }) => {
    await page.goto('/clustering/create/');

    await page.click('a:has-text("Cancel")');

    await expect(page).toHaveURL(/\/clustering\/$/);
  });

  // Skip: Requires segmentation fixtures
  test.skip('create single-segmentation run', async ({ page }) => {
    // This test requires:
    // - At least one recording with a completed segmentation
    // See battycoda-hxh for fixture creation

    await page.goto('/clustering/create/');

    // Fill in name
    await page.fill('#name', 'E2E Test Clustering Run');

    // Select algorithm
    await page.selectOption('#algorithm', { label: /K-Means/ });

    // Set number of clusters
    await page.fill('#n_clusters', '5');

    // Select segmentation (first available)
    await page.selectOption('#segmentation', { index: 1 });

    // Submit
    await page.click('button[type="submit"]');

    // Should redirect to run detail or dashboard
    await expect(page).toHaveURL(/\/clustering\/(run\/\d+)?/);
  });

  // Skip: Requires project with segmented recordings
  test.skip('create project-level run', async ({ page }) => {
    // This test requires:
    // - At least one project with recordings
    // - Recordings must have completed segmentations
    // See battycoda-hxh for fixture creation

    await page.goto('/clustering/create/');

    // Fill in name
    await page.fill('#name', 'E2E Test Project Clustering');

    // Switch to project scope
    await page.click('label[for="scope_project"]');

    // Wait for animation
    await page.waitForTimeout(400);

    // Select project
    await page.selectOption('#project', { label: /E2E Test Project/ });

    // Wait for project data to load
    await page.waitForTimeout(500);

    // Select algorithm
    await page.selectOption('#algorithm', { label: /K-Means/ });

    // Submit
    await page.click('button[type="submit"]');

    // Should redirect to run detail or show success
    await expect(page).toHaveURL(/\/clustering\/(run\/\d+)?/);
  });
});

test.describe('Cluster Explorer - Authenticated', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, users.testUser.username, users.testUser.password);
  });

  // Skip: Requires a completed clustering run
  test.skip('visualization renders', async ({ page }) => {
    // This test requires:
    // - At least one completed clustering run with clusters
    // See battycoda-hxh for fixture creation

    // Navigate to an existing clustering run's explorer
    await page.goto('/clustering/explorer/1/');

    // Wait for visualization to load
    await expect(page.locator('#cluster-visualization')).toBeVisible();

    // SVG should be rendered
    await expect(page.locator('#cluster-visualization svg')).toBeVisible();
  });

  // Skip: Requires a completed clustering run
  test.skip('cluster selection updates details panel', async ({ page }) => {
    // This test requires:
    // - At least one completed clustering run with clusters

    await page.goto('/clustering/explorer/1/');

    // Wait for visualization
    await page.waitForSelector('#cluster-visualization svg');

    // Click on a cluster point
    await page.click('circle:first-child');

    // Details panel should update
    await expect(page.locator('.cluster-details')).not.toHaveClass(/d-none/);
    await expect(page.locator('.cluster-id-display')).toBeVisible();
  });

  // Skip: Requires a completed clustering run
  test.skip('controls affect visualization', async ({ page }) => {
    // This test requires:
    // - At least one completed clustering run with clusters

    await page.goto('/clustering/explorer/1/');

    // Wait for visualization
    await page.waitForSelector('#cluster-visualization svg');

    // Adjust point size slider
    await page.fill('#point-size', '10');

    // Adjust opacity slider
    await page.fill('#cluster-opacity', '0.5');

    // Points should still be visible (hard to verify visual changes)
    await expect(page.locator('circle').first()).toBeVisible();
  });

  // Skip: Requires a completed clustering run
  test.skip('export dropdown shows options', async ({ page }) => {
    // This test requires:
    // - At least one completed clustering run

    await page.goto('/clustering/explorer/1/');

    // Click export dropdown
    await page.click('button:has-text("Export")');

    // Export options should be visible
    await expect(
      page.locator('a.dropdown-item:has-text("Export Clusters as CSV")')
    ).toBeVisible();
    await expect(
      page.locator('a.dropdown-item:has-text("Export Mappings as CSV")')
    ).toBeVisible();
  });
});

test.describe('Cluster Mapping - Authenticated', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, users.testUser.username, users.testUser.password);
  });

  // Skip: Requires a completed clustering run
  test.skip('mapping interface loads', async ({ page }) => {
    // This test requires:
    // - At least one completed clustering run with clusters

    await page.goto('/clustering/mapping/1/');

    // Should show mapping interface
    await expect(page.locator('h3.card-title')).toContainText('Map Clusters');

    // Should show clusters and call types
    await expect(page.locator('.cluster-list, .clusters')).toBeVisible();
    await expect(page.locator('.call-types, .call-type-list')).toBeVisible();
  });

  // Skip: Requires a completed clustering run with drag-drop UI
  test.skip('drag cluster to call type creates mapping', async ({ page }) => {
    // This test requires:
    // - At least one completed clustering run
    // - The mapping interface supports drag-drop

    await page.goto('/clustering/mapping/1/');

    // Drag and drop
    const cluster = page.locator('.cluster-item:first-child');
    const callType = page.locator('.call-type-drop:first-child');

    await cluster.dragTo(callType);

    // Mapping should be created
    await expect(
      page.locator('.mapping-item, .alert-success, .toast-success')
    ).toBeVisible();
  });
});

test.describe('Clustering Run Detail - Authenticated', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, users.testUser.username, users.testUser.password);
  });

  // Skip: Requires an existing clustering run
  test.skip('run detail page shows run information', async ({ page }) => {
    // This test requires:
    // - At least one clustering run (any status)

    await page.goto('/clustering/run/1/');

    // Should show run details
    await expect(page.locator('h3.card-title')).toContainText('Clustering Run:');

    // Should show run details table
    await expect(page.locator('th:has-text("Name")')).toBeVisible();
    await expect(page.locator('th:has-text("Status")')).toBeVisible();
    await expect(page.locator('th:has-text("Algorithm")')).toBeVisible();
  });

  // Skip: Requires a completed clustering run
  test.skip('completed run shows results and action buttons', async ({
    page,
  }) => {
    // This test requires:
    // - At least one completed clustering run

    await page.goto('/clustering/run/1/');

    // Should show results summary
    await expect(page.locator('h4:has-text("Results Summary")')).toBeVisible();
    await expect(
      page.locator('th:has-text("Segments Processed")')
    ).toBeVisible();
    await expect(page.locator('th:has-text("Clusters Created")')).toBeVisible();

    // Should show action buttons
    await expect(
      page.locator('a:has-text("Explore Clusters")')
    ).toBeVisible();
    await expect(
      page.locator('a:has-text("Map to Call Types")')
    ).toBeVisible();
  });
});
