import { test, expect } from '@playwright/test';
import { login } from '../helpers/auth.js';
import users from '../fixtures/users.json' with { type: 'json' };

/**
 * End-to-end tests for task annotation workflows.
 *
 * NOTE: Some tests require additional fixtures that are not yet set up:
 * - Task batches with tasks
 * - Completed segmentations with segments
 * - Classification runs
 *
 * Tests that require these fixtures are marked with test.skip() and describe
 * what fixtures are needed. See battycoda-hxh bead for fixture creation work.
 */

test.describe('Tasks - Unauthenticated', () => {
  test('task batches page redirects to login when not authenticated', async ({
    page,
  }) => {
    await page.goto('/tasks/batches/');

    // Should redirect to login
    await expect(page).toHaveURL(/\/accounts\/login/);

    // Should show login form
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
  });

  test('task batch detail redirects to login when not authenticated', async ({
    page,
  }) => {
    // Try to access batch detail (ID 1 may not exist, but should redirect regardless)
    await page.goto('/tasks/batches/1/');

    // Should redirect to login
    await expect(page).toHaveURL(/\/accounts\/login/);
  });

  test('task batch review redirects to login when not authenticated', async ({
    page,
  }) => {
    await page.goto('/tasks/batches/1/review/');

    // Should redirect to login
    await expect(page).toHaveURL(/\/accounts\/login/);
  });

  test('annotate task redirects to login when not authenticated', async ({
    page,
  }) => {
    await page.goto('/tasks/annotate/1/');

    // Should redirect to login
    await expect(page).toHaveURL(/\/accounts\/login/);
  });

  test('task detail redirects to login when not authenticated', async ({
    page,
  }) => {
    await page.goto('/tasks/1/');

    // Should redirect to login
    await expect(page).toHaveURL(/\/accounts\/login/);
  });

  test('get next task redirects to login when not authenticated', async ({
    page,
  }) => {
    await page.goto('/tasks/next/');

    // Should redirect to login
    await expect(page).toHaveURL(/\/accounts\/login/);
  });
});

test.describe('Task Batches - Authenticated', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, users.testUser.username, users.testUser.password);
  });

  test('displays task batches list page', async ({ page }) => {
    await page.goto('/tasks/batches/');

    // Should show the task batches page with title (h5 is used in list_view_base.html)
    await expect(page.locator('h5.card-title')).toContainText('All Task Batches');
  });

  test('shows empty state when no task batches exist', async ({ page }) => {
    await page.goto('/tasks/batches/');

    // Either shows batches table or empty state message
    const batchesTable = page.locator('table:has(th:has-text("Name"))');
    const emptyMessage = page.locator('.text-center:has-text("No Task Batches Found")');

    // One of these should be visible
    const hasBatches = await batchesTable.isVisible();
    const hasEmptyMessage = await emptyMessage.isVisible();

    expect(hasBatches || hasEmptyMessage).toBe(true);
  });

  test('has create from classification link', async ({ page }) => {
    await page.goto('/tasks/batches/');

    // Should have a link to create task batch from classification
    await expect(
      page.locator('a:has-text("Create from Classification")')
    ).toBeVisible();
  });

  test('has download completed batches button', async ({ page }) => {
    await page.goto('/tasks/batches/');

    // Should have a download button
    await expect(
      page.locator('a:has-text("Download Completed Batches")')
    ).toBeVisible();
  });

  test('has project filter dropdown', async ({ page }) => {
    await page.goto('/tasks/batches/');

    // Should have a project filter dropdown
    await expect(page.locator('#project-filter')).toBeVisible();
  });

  test('create from classification link navigates correctly', async ({
    page,
  }) => {
    await page.goto('/tasks/batches/');

    await page.click('a:has-text("Create from Classification")');

    // Should navigate to classification home
    await expect(page).toHaveURL(/\/classification\//);
  });
});

test.describe('Task Batch Detail - Authenticated', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, users.testUser.username, users.testUser.password);
  });

  // Skip: Requires a task batch fixture
  test.skip('batch detail page shows batch information', async ({ page }) => {
    // This test requires:
    // - At least one task batch
    // See battycoda-hxh for fixture creation

    await page.goto('/tasks/batches/1/');

    // Should show batch details
    await expect(page.locator('h2:has-text("Batch Information")')).toBeVisible();

    // Should show batch metadata
    await expect(page.locator('text=Recording:')).toBeVisible();
    await expect(page.locator('text=Species:')).toBeVisible();
    await expect(page.locator('text=Project:')).toBeVisible();
  });

  // Skip: Requires a task batch fixture
  test.skip('batch detail page shows action buttons', async ({ page }) => {
    // This test requires:
    // - At least one task batch

    await page.goto('/tasks/batches/1/');

    // Should show action buttons
    await expect(page.locator('a:has-text("Annotate Tasks")')).toBeVisible();
    await expect(page.locator('a:has-text("Review & Relabel")')).toBeVisible();
    await expect(page.locator('a:has-text("Export Results")')).toBeVisible();
    await expect(page.locator('button:has-text("Delete Batch")')).toBeVisible();
  });

  // Skip: Requires a task batch with tasks
  test.skip('batch detail page shows tasks table', async ({ page }) => {
    // This test requires:
    // - At least one task batch with tasks

    await page.goto('/tasks/batches/1/');

    // Should show tasks table
    await expect(page.locator('h3:has-text("Tasks in this Batch")')).toBeVisible();
    await expect(page.locator('table:has(th:has-text("Segment"))')).toBeVisible();
    await expect(page.locator('table:has(th:has-text("Status"))')).toBeVisible();
    await expect(page.locator('table:has(th:has-text("Label"))')).toBeVisible();
  });

  // Skip: Requires a task batch
  test.skip('annotate tasks button navigates to annotation', async ({
    page,
  }) => {
    // This test requires:
    // - At least one task batch with tasks

    await page.goto('/tasks/batches/1/');

    await page.click('a:has-text("Annotate Tasks")');

    // Should navigate to annotation page
    await expect(page).toHaveURL(/\/tasks\/(annotate\/\d+|batch\/\d+\/annotate)/);
  });

  // Skip: Requires a task batch
  test.skip('review button navigates to review page', async ({ page }) => {
    // This test requires:
    // - At least one task batch

    await page.goto('/tasks/batches/1/');

    await page.click('a:has-text("Review & Relabel")');

    // Should navigate to review page
    await expect(page).toHaveURL(/\/tasks\/batches\/\d+\/review/);
  });

  // Skip: Requires a task batch
  test.skip('delete batch button shows confirmation modal', async ({
    page,
  }) => {
    // This test requires:
    // - At least one task batch

    await page.goto('/tasks/batches/1/');

    await page.click('button:has-text("Delete Batch")');

    // Modal should appear
    await expect(page.locator('#deleteBatchModal')).toBeVisible();
    await expect(page.locator('text=Are you sure you want to delete')).toBeVisible();
  });
});

test.describe('Task Batch Review - Authenticated', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, users.testUser.username, users.testUser.password);
  });

  // Skip: Requires a task batch fixture
  test.skip('review page loads', async ({ page }) => {
    // This test requires:
    // - At least one task batch with tasks

    await page.goto('/tasks/batches/1/review/');

    // Should show review interface
    await expect(page.locator('h1, h2, h3').first()).toBeVisible();
  });
});

test.describe('Task Annotation Interface - Authenticated', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, users.testUser.username, users.testUser.password);
  });

  // Skip: Requires a task fixture
  test.skip('annotation page loads with spectrogram', async ({ page }) => {
    // This test requires:
    // - At least one task with valid audio data

    await page.goto('/tasks/annotate/1/');

    // Should show task info
    await expect(page.locator('h4:has-text("Task #")')).toBeVisible();

    // Should show spectrogram container
    await expect(page.locator('#spectrogram-container')).toBeVisible();

    // Should show audio player
    await expect(page.locator('#audio-player')).toBeVisible();
  });

  // Skip: Requires a task fixture
  test.skip('annotation page shows classification form', async ({ page }) => {
    // This test requires:
    // - At least one task

    await page.goto('/tasks/annotate/1/');

    // Should show classification section
    await expect(page.locator('h4:has-text("Task Classification")')).toBeVisible();

    // Should show call type selection
    await expect(page.locator('h5:has-text("Select Label")')).toBeVisible();

    // Should have submit button
    await expect(page.locator('button:has-text("Mark as Done")')).toBeVisible();
  });

  // Skip: Requires a task fixture
  test.skip('annotation page shows task metadata', async ({ page }) => {
    // This test requires:
    // - At least one task

    await page.goto('/tasks/annotate/1/');

    // Should show task metadata in sidebar
    await expect(page.locator('text=Species:')).toBeVisible();
    await expect(page.locator('text=Recording:')).toBeVisible();
    await expect(page.locator('text=Segment:')).toBeVisible();
  });

  // Skip: Requires a task fixture
  test.skip('annotation page has view controls', async ({ page }) => {
    // This test requires:
    // - At least one task

    await page.goto('/tasks/annotate/1/');

    // Should have detail/overview buttons
    await expect(page.locator('#detail-view-btn')).toBeVisible();
    await expect(page.locator('#overview-btn')).toBeVisible();

    // Should have channel buttons
    await expect(page.locator('#channel-1-btn')).toBeVisible();
    await expect(page.locator('#channel-2-btn')).toBeVisible();
  });

  // Skip: Requires a task fixture
  test.skip('detail view button toggles spectrogram view', async ({ page }) => {
    // This test requires:
    // - At least one task

    await page.goto('/tasks/annotate/1/');

    // Click detail view button
    await page.click('#detail-view-btn');

    // Button should become active
    await expect(page.locator('#detail-view-btn')).toHaveClass(/active/);
  });

  // Skip: Requires a task fixture
  test.skip('channel buttons toggle audio channel', async ({ page }) => {
    // This test requires:
    // - At least one task

    await page.goto('/tasks/annotate/1/');

    // Click channel 2 button
    await page.click('#channel-2-btn');

    // Channel 2 button should become active
    await expect(page.locator('#channel-2-btn')).toHaveClass(/active/);
    await expect(page.locator('#channel-1-btn')).not.toHaveClass(/active/);
  });

  // Skip: Requires a task fixture
  test.skip('navigation links work in annotation sidebar', async ({ page }) => {
    // This test requires:
    // - At least one task with a batch

    await page.goto('/tasks/annotate/1/');

    // Should have navigation buttons
    await expect(page.locator('a:has-text("Return to Batch")')).toBeVisible();
    await expect(page.locator('a:has-text("Next Task")')).toBeVisible();
  });

  // Skip: Requires multiple tasks
  test.skip('next task link navigates to next task', async ({ page }) => {
    // This test requires:
    // - At least two tasks

    await page.goto('/tasks/annotate/1/');

    await page.click('a:has-text("Next Task")');

    // Should navigate to a different task or show no more tasks message
    await page.waitForLoadState('networkidle');
  });

  // Skip: Requires a task fixture
  test.skip('selecting call type and submitting marks task done', async ({
    page,
  }) => {
    // This test requires:
    // - At least one task that is not yet done

    await page.goto('/tasks/annotate/1/');

    // Select a call type (Unknown is always available)
    await page.click('#Unknown');

    // Submit the form
    await page.click('button:has-text("Mark as Done")');

    // Should navigate to next task or show success
    await page.waitForLoadState('networkidle');
  });
});

test.describe('Task Navigation - Authenticated', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, users.testUser.username, users.testUser.password);
  });

  // Skip: Requires task fixtures
  test.skip('get next task redirects to annotation page', async ({ page }) => {
    // This test requires:
    // - At least one pending task

    await page.goto('/tasks/next/');

    // Should redirect to annotation page or show no tasks message
    const url = page.url();
    expect(
      url.includes('/tasks/annotate/') || url.includes('/tasks/batches/')
    ).toBe(true);
  });

  // Skip: Requires task fixtures
  test.skip('get last task redirects to annotation page', async ({ page }) => {
    // This test requires:
    // - At least one task that was previously viewed

    await page.goto('/tasks/last/');

    // Should redirect to last viewed task or show error
    await page.waitForLoadState('networkidle');
  });

  // Skip: Requires task fixtures
  test.skip('annotate batch redirects to first task in batch', async ({
    page,
  }) => {
    // This test requires:
    // - At least one task batch with tasks

    await page.goto('/tasks/batch/1/annotate/');

    // Should redirect to first task in the batch
    await expect(page).toHaveURL(/\/tasks\/annotate\/\d+/);
  });

  // Skip: Requires task fixtures
  test.skip('skip to next batch navigates to different batch', async ({
    page,
  }) => {
    // This test requires:
    // - At least two task batches with tasks

    await page.goto('/tasks/1/skip-batch/');

    // Should navigate to task in a different batch
    await page.waitForLoadState('networkidle');
  });
});

test.describe('Task Detail - Authenticated', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, users.testUser.username, users.testUser.password);
  });

  // Skip: Requires a task fixture
  test.skip('task detail page shows task information', async ({ page }) => {
    // This test requires:
    // - At least one task

    await page.goto('/tasks/1/');

    // Should show task details
    await expect(page.locator('h1, h2').first()).toContainText('Task');
  });
});
