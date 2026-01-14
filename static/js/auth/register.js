/**
 * Registration form validation and AJAX checks
 * Handles username and email validation, availability checks
 */
document.addEventListener('DOMContentLoaded', function () {
  const usernameField = document.getElementById('id_username');
  const emailField = document.getElementById('id_email');
  const submitButton = document.querySelector('button[type="submit"]');
  let usernameTypingTimer; // Timer identifier for username
  let emailTypingTimer; // Timer identifier for email
  const doneTypingInterval = 500; // Time in ms (0.5 seconds)

  // Username validation and checking
  if (usernameField) {
    // Get the warning element
    const usernameWarningElement = document.getElementById('username-warning');

    // On input event, validate characters and remove @ symbols
    usernameField.addEventListener('input', function (e) {
      // Clear any typing timer
      clearTimeout(usernameTypingTimer);

      // Remove @ symbol if present
      if (this.value.includes('@')) {
        this.value = this.value.replace(/@/g, '');
        usernameWarningElement.textContent = 'Username cannot contain the @ symbol.';
      }

      // Only letters, numbers, and ._-
      const regex = /^[\w.-]*$/;
      if (!regex.test(this.value)) {
        this.value = this.value.replace(/[^\w.-]/g, '');
        usernameWarningElement.textContent =
          'Username can only contain letters, numbers, and the characters ._-';
      }

      // Start timer to check if username exists (wait for user to finish typing)
      if (this.value.length > 0) {
        usernameTypingTimer = setTimeout(
          () => checkUsername(usernameCheckURL, csrfToken),
          doneTypingInterval
        );
      } else {
        usernameWarningElement.textContent = '';
      }
    });

    // Also run the check when the field loses focus
    usernameField.addEventListener('blur', function () {
      clearTimeout(usernameTypingTimer);
      if (this.value.length > 0) {
        checkUsername(usernameCheckURL, csrfToken);
      }
    });
  }

  // Email validation and checking
  if (emailField) {
    // Get the warning element
    const emailWarningElement = document.getElementById('email-warning');

    // On input event for email
    emailField.addEventListener('input', function (e) {
      // Clear any typing timer
      clearTimeout(emailTypingTimer);

      // Start timer to check if email exists (wait for user to finish typing)
      if (this.value.length > 0) {
        emailTypingTimer = setTimeout(
          () => checkEmail(emailCheckURL, csrfToken),
          doneTypingInterval
        );
      } else {
        emailWarningElement.textContent = '';
      }
    });

    // Also run the check when the field loses focus
    emailField.addEventListener('blur', function () {
      clearTimeout(emailTypingTimer);
      if (this.value.length > 0) {
        checkEmail(emailCheckURL, csrfToken);
      }
    });
  }

  /**
   * Check if username is valid and available
   * @param {string} url - The URL to send the check request to
   * @param {string} csrfToken - CSRF token for security
   */
  function checkUsername(url, csrfToken) {
    const username = usernameField.value;
    const usernameWarningElement = document.getElementById('username-warning');

    if (username.length > 0) {
      // Create form data
      const formData = new FormData();
      formData.append('username', username);
      formData.append('csrfmiddlewaretoken', csrfToken);

      // Send AJAX request
      fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          Accept: 'application/json',
        },
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          return response.json();
        })
        .then((data) => {
          if (!data.valid) {
            usernameWarningElement.textContent = data.message;
            submitButton.disabled = true;
          } else if (data.exists) {
            usernameWarningElement.textContent = data.message;
            submitButton.disabled = true;
          } else {
            usernameWarningElement.textContent = '';
            // Only enable submit if email check is also OK
            if (!document.getElementById('email-warning').textContent) {
              submitButton.disabled = false;
            }
          }
        })
        .catch((error) => {
          console.error('Error checking username:', error);
          usernameWarningElement.textContent = 'Error checking username. Please try again.';
        });
    }
  }

  /**
   * Check if email is available
   * @param {string} url - The URL to send the check request to
   * @param {string} csrfToken - CSRF token for security
   */
  function checkEmail(url, csrfToken) {
    const email = emailField.value;
    const emailWarningElement = document.getElementById('email-warning');

    if (email.length > 0) {
      // Create form data
      const formData = new FormData();
      formData.append('email', email);
      formData.append('csrfmiddlewaretoken', csrfToken);

      // Send AJAX request
      fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          Accept: 'application/json',
        },
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          return response.json();
        })
        .then((data) => {
          if (data.exists) {
            emailWarningElement.textContent = data.message;
            submitButton.disabled = true;
          } else {
            emailWarningElement.textContent = '';
            // Only enable submit if username check is also OK
            if (!document.getElementById('username-warning').textContent) {
              submitButton.disabled = false;
            }
          }
        })
        .catch((error) => {
          console.error('Error checking email:', error);
          emailWarningElement.textContent = 'Error checking email. Please try again.';
        });
    }
  }
});
