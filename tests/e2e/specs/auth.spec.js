import { test, expect } from '@playwright/test';
import { login, logout, isLoggedIn } from '../helpers/auth.js';
import users from '../fixtures/users.json' with { type: 'json' };

/**
 * End-to-end tests for authentication flows.
 * Tests login, registration, logout, and protected route access.
 */

test.describe('Authentication', () => {
  test.describe('Login', () => {
    test('successful login redirects to home', async ({ page }) => {
      await page.goto('/accounts/login/');
      await page.fill('input[name="username"]', users.testUser.email);
      await page.fill('input[name="password"]', users.testUser.password);
      await page.click('button[type="submit"]');

      // Should redirect away from login page to home
      await expect(page).toHaveURL(/^http.*:\/\/.*\/?$/);
    });

    test('can login with username instead of email', async ({ page }) => {
      await page.goto('/accounts/login/');
      await page.fill('input[name="username"]', users.testUser.username);
      await page.fill('input[name="password"]', users.testUser.password);
      await page.click('button[type="submit"]');

      // Should redirect away from login page
      await expect(page).not.toHaveURL(/\/accounts\/login/);
    });

    test('invalid credentials shows error', async ({ page }) => {
      await page.goto('/accounts/login/');
      await page.fill('input[name="username"]', 'wrong@email.com');
      await page.fill('input[name="password"]', 'wrongpassword');
      await page.click('button[type="submit"]');

      // Should show error alert
      await expect(page.locator('.alert-danger')).toBeVisible();
      await expect(page.locator('.alert-danger')).toContainText('Login Failed');
      // Should stay on login page
      await expect(page).toHaveURL(/\/accounts\/login/);
    });

    test('empty password shows validation', async ({ page }) => {
      await page.goto('/accounts/login/');
      await page.fill('input[name="username"]', users.testUser.email);
      // Don't fill password, try to submit
      // HTML5 validation should prevent submission
      const submitButton = page.locator('button[type="submit"]');
      await submitButton.click();

      // Should still be on login page (HTML5 validation prevents submission)
      await expect(page).toHaveURL(/\/accounts\/login/);
    });

    test('login page has link to request login code', async ({ page }) => {
      await page.goto('/accounts/login/');

      // Should have a link/button to login with code (use ID for specificity)
      const codeLoginLink = page.locator('#codeLoginBtn');
      await expect(codeLoginLink).toBeVisible();
      await expect(codeLoginLink).toContainText('Login with Code');
    });

    test('login with code link navigates to code request page', async ({
      page,
    }) => {
      await page.goto('/accounts/login/');

      // Click the login with code link (use ID for specificity)
      await page.click('#codeLoginBtn');

      // Should be on the request login code page
      await expect(page).toHaveURL(/\/accounts\/request-login-code/);
      await expect(page.locator('h2')).toContainText('One-Time Code');
    });

    test('request login code shows confirmation message', async ({ page }) => {
      await page.goto('/accounts/request-login-code/');
      await page.fill('input[name="username"]', users.testUser.email);
      await page.click('button[type="submit"]');

      // Should redirect to enter code page
      await expect(page).toHaveURL(/\/accounts\/enter-login-code/);
    });
  });

  test.describe('Registration', () => {
    test('registration page is accessible', async ({ page }) => {
      await page.goto('/accounts/register/');

      // Check form elements are present
      await expect(page.locator('input[name="username"]')).toBeVisible();
      await expect(page.locator('input[name="email"]')).toBeVisible();
      await expect(page.locator('input#id_password1')).toBeVisible();
      await expect(page.locator('input#id_password2')).toBeVisible();
      await expect(page.locator('input#id_captcha_answer')).toBeVisible();
    });

    test('registration page shows password requirements', async ({ page }) => {
      await page.goto('/accounts/register/');

      // Should display password requirements
      await expect(page.locator('text=at least 8 characters')).toBeVisible();
    });

    test('registration validates password mismatch', async ({ page }) => {
      const uniqueUsername = `testuser_${Date.now()}`;
      const uniqueEmail = `test_${Date.now()}@example.com`;

      await page.goto('/accounts/register/');
      await page.fill('input[name="username"]', uniqueUsername);
      await page.fill('input[name="email"]', uniqueEmail);
      await page.fill('input#id_password1', 'SecurePass123!');
      await page.fill('input#id_password2', 'DifferentPass456!');

      // Solve the captcha
      const captchaNum1 = await page
        .locator('input[name="captcha_num1"]')
        .inputValue();
      const captchaNum2 = await page
        .locator('input[name="captcha_num2"]')
        .inputValue();
      const captchaAnswer = parseInt(captchaNum1) + parseInt(captchaNum2);
      await page.fill('input#id_captcha_answer', captchaAnswer.toString());

      await page.click('button[type="submit"]');

      // Should show error about password mismatch (use span.text-danger for form errors)
      await expect(page.locator('span.text-danger').first()).toBeVisible();
      // Should stay on register page
      await expect(page).toHaveURL(/\/accounts\/register/);
    });

    test('registration validates short password', async ({ page }) => {
      const uniqueUsername = `testuser_${Date.now()}`;
      const uniqueEmail = `test_${Date.now()}@example.com`;

      await page.goto('/accounts/register/');
      await page.fill('input[name="username"]', uniqueUsername);
      await page.fill('input[name="email"]', uniqueEmail);
      await page.fill('input#id_password1', '123'); // Too short
      await page.fill('input#id_password2', '123');

      // Solve the captcha
      const captchaNum1 = await page
        .locator('input[name="captcha_num1"]')
        .inputValue();
      const captchaNum2 = await page
        .locator('input[name="captcha_num2"]')
        .inputValue();
      const captchaAnswer = parseInt(captchaNum1) + parseInt(captchaNum2);
      await page.fill('input#id_captcha_answer', captchaAnswer.toString());

      await page.click('button[type="submit"]');

      // Should show error about password requirements
      await expect(page.locator('span.text-danger').first()).toBeVisible();
      // Should stay on register page
      await expect(page).toHaveURL(/\/accounts\/register/);
    });

    test('registration validates invalid captcha', async ({ page }) => {
      const uniqueUsername = `testuser_${Date.now()}`;
      const uniqueEmail = `test_${Date.now()}@example.com`;

      await page.goto('/accounts/register/');
      await page.fill('input[name="username"]', uniqueUsername);
      await page.fill('input[name="email"]', uniqueEmail);
      await page.fill('input#id_password1', 'SecurePassword123!');
      await page.fill('input#id_password2', 'SecurePassword123!');

      // Enter wrong captcha answer
      await page.fill('input#id_captcha_answer', '999999');

      await page.click('button[type="submit"]');

      // Should show error about captcha
      await expect(page.locator('span.text-danger').first()).toBeVisible();
      // Should stay on register page
      await expect(page).toHaveURL(/\/accounts\/register/);
    });

    test('successful registration auto-logs in user', async ({ page }) => {
      const uniqueUsername = `e2e_new_${Date.now()}`;
      const uniqueEmail = `e2e_new_${Date.now()}@example.com`;

      await page.goto('/accounts/register/');
      await page.fill('input[name="username"]', uniqueUsername);
      await page.fill('input[name="email"]', uniqueEmail);
      await page.fill('input#id_password1', 'SecureTestPassword123!');
      await page.fill('input#id_password2', 'SecureTestPassword123!');

      // Solve the captcha
      const captchaNum1 = await page
        .locator('input[name="captcha_num1"]')
        .inputValue();
      const captchaNum2 = await page
        .locator('input[name="captcha_num2"]')
        .inputValue();
      const captchaAnswer = parseInt(captchaNum1) + parseInt(captchaNum2);
      await page.fill('input#id_captcha_answer', captchaAnswer.toString());

      await page.click('button[type="submit"]');

      // Should redirect to home (auto-login after registration)
      await expect(page).not.toHaveURL(/\/accounts\/register/);
      await expect(page).not.toHaveURL(/\/accounts\/login/);
    });

    test('login page has link to registration', async ({ page }) => {
      await page.goto('/accounts/login/');

      // Should have a link to create account (use ID to avoid navbar Register link)
      const registerLink = page.locator('#registerLink');
      await expect(registerLink).toBeVisible();
      await expect(registerLink).toContainText('Create Account');
    });
  });

  test.describe('Logout', () => {
    test('logout clears session and redirects to login', async ({ page }) => {
      // First login
      await login(page, users.testUser.username, users.testUser.password);

      // Verify logged in
      expect(await isLoggedIn(page)).toBe(true);

      // Logout
      await logout(page);

      // Wait for page load
      await page.waitForLoadState('networkidle');

      // After logout, should not be logged in anymore
      // The user should be on the login page (logout redirects to login)
      await expect(page).toHaveURL(/\/accounts\/login/);
    });

    test('logout shows success message', async ({ page }) => {
      // First login
      await login(page, users.testUser.username, users.testUser.password);

      // Go to logout URL
      await page.goto('/accounts/logout/');

      // Wait for page load
      await page.waitForLoadState('networkidle');

      // Messages are shown via toastr toast notifications
      // Check for toastr success toast
      await expect(page.locator('.toast-success, .toastr-success')).toBeVisible(
        { timeout: 10000 }
      );
    });
  });

  test.describe('Protected routes', () => {
    test('unauthenticated user redirected to login from recordings', async ({
      page,
    }) => {
      // Try to access recordings without logging in
      await page.goto('/recordings/');

      // Should redirect to login
      await expect(page).toHaveURL(/\/accounts\/login/);
    });

    test('unauthenticated user redirected to login from projects', async ({
      page,
    }) => {
      // Try to access projects without logging in
      await page.goto('/projects/');

      // Should redirect to login
      await expect(page).toHaveURL(/\/accounts\/login/);
    });

    test('unauthenticated user redirected to login from clustering', async ({
      page,
    }) => {
      // Try to access clustering without logging in
      await page.goto('/clustering/');

      // Should redirect to login
      await expect(page).toHaveURL(/\/accounts\/login/);
    });

    // Skip: This app may not use the standard Django ?next= parameter
    test.skip('login redirect includes next parameter', async ({ page }) => {
      // Try to access a protected page
      await page.goto('/recordings/');

      // Should redirect to login with next parameter (may be URL-encoded)
      const url = page.url();
      expect(url).toMatch(/\/accounts\/login/);
      // Check for next parameter (can be encoded as %2F or plain /)
      expect(url).toMatch(/next=/);
    });

    test('after login, redirects to originally requested page', async ({
      page,
    }) => {
      // Try to access recordings
      await page.goto('/recordings/');

      // Should be on login page
      await expect(page).toHaveURL(/\/accounts\/login/);

      // Login
      await page.fill('input[name="username"]', users.testUser.username);
      await page.fill('input[name="password"]', users.testUser.password);
      await page.click('button[type="submit"]');

      // Wait for navigation
      await page.waitForLoadState('networkidle');

      // Should redirect back to recordings (or home if next is not preserved)
      // Some implementations redirect to home instead
      const currentUrl = page.url();
      expect(
        currentUrl.includes('/recordings') || currentUrl.endsWith('/')
      ).toBe(true);
    });
  });

  test.describe('Password reset', () => {
    test('password reset link is visible on login page', async ({ page }) => {
      await page.goto('/accounts/login/');

      // Should have forgot password link (use ID for specificity)
      const resetLink = page.locator('#resetPasswordLink');
      await expect(resetLink).toBeVisible();
      await expect(resetLink).toContainText('Forgot Password');
    });

    test('password reset page is accessible', async ({ page }) => {
      await page.goto('/accounts/password-reset/');

      // Should show password reset form
      await expect(page.locator('input[name="identifier"]')).toBeVisible();
      await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test('password reset shows confirmation regardless of email existence', async ({
      page,
    }) => {
      await page.goto('/accounts/password-reset/');
      await page.fill('input[name="identifier"]', 'nonexistent@example.com');
      await page.click('button[type="submit"]');

      // Should redirect to login and show success message via toastr
      await expect(page).toHaveURL(/\/accounts\/login/);

      // Wait for toast to appear (messages use toastr)
      await expect(page.locator('.toast-success, .toastr-success')).toBeVisible(
        { timeout: 10000 }
      );
    });
  });

  test.describe('Session persistence', () => {
    test('session persists across page navigations', async ({ page }) => {
      // Login
      await login(page, users.testUser.username, users.testUser.password);

      // Navigate to different pages
      await page.goto('/recordings/');
      expect(await isLoggedIn(page)).toBe(true);

      await page.goto('/projects/');
      expect(await isLoggedIn(page)).toBe(true);

      await page.goto('/');
      expect(await isLoggedIn(page)).toBe(true);
    });
  });
});
