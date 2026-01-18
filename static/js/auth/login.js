/**
 * Login Page Module
 *
 * Handles transferring username/email to related pages:
 * - Login with code page
 * - Password reset page
 * - Registration page
 *
 * Usage:
 * Include this script on the login page with URL data:
 * <script id="login-page-data" type="application/json">
 * {
 *   "loginCodeUrl": "{% url 'battycoda_app:request_login_code' %}",
 *   "passwordResetUrl": "{% url 'battycoda_app:password_reset_request' %}",
 *   "registerUrl": "{% url 'battycoda_app:register' %}"
 * }
 * </script>
 * <script src="{% static 'js/auth/login.js' %}"></script>
 */

/**
 * Get URL configuration from page data
 * @returns {Object} URLs for navigation
 */
function getUrlConfig() {
  const dataElement = document.getElementById('login-page-data');
  if (!dataElement) {
    console.warn('login-page-data element not found');
    return {};
  }
  try {
    return JSON.parse(dataElement.textContent);
  } catch (e) {
    console.error('Error parsing login page data:', e);
    return {};
  }
}

/**
 * Setup click handlers for transferring username to related pages
 */
function setupUsernameTransfer() {
  const codeLoginBtn = document.getElementById('codeLoginBtn');
  const resetPasswordLink = document.getElementById('resetPasswordLink');
  const registerLink = document.getElementById('registerLink');
  const usernameField = document.getElementById('id_username');

  const urls = getUrlConfig();

  // Handle login with code button
  if (codeLoginBtn && urls.loginCodeUrl) {
    codeLoginBtn.addEventListener('click', function (e) {
      if (usernameField && usernameField.value) {
        e.preventDefault();
        const username = encodeURIComponent(usernameField.value);
        window.location.href = urls.loginCodeUrl + '?username=' + username;
      }
    });
  }

  // Handle password reset link
  if (resetPasswordLink && urls.passwordResetUrl) {
    resetPasswordLink.addEventListener('click', function (e) {
      if (usernameField && usernameField.value) {
        e.preventDefault();
        const username = encodeURIComponent(usernameField.value);
        window.location.href = urls.passwordResetUrl + '?username=' + username;
      }
    });
  }

  // Handle register link
  if (registerLink && urls.registerUrl) {
    registerLink.addEventListener('click', function (e) {
      if (usernameField && usernameField.value) {
        e.preventDefault();
        const identifier = usernameField.value;

        // Check if it looks like an email
        if (identifier.includes('@')) {
          window.location.href = urls.registerUrl + '?email=' + encodeURIComponent(identifier);
        } else {
          window.location.href = urls.registerUrl + '?username=' + encodeURIComponent(identifier);
        }
      }
    });
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', setupUsernameTransfer);
} else {
  setupUsernameTransfer();
}
